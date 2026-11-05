// Website form mailer. Runs from one Google account and serves every client site.
//
// Each site sends its form here with a Site ID. The "Clients" tab of the Google
// Sheet matches that ID to the inbox that gets the email. The address never comes
// from the website, so nobody can use this to email anyone else.
//
// To add a client, add one row to the Clients tab. No code change or redeploy needed.

var CLIENTS_TAB = "Clients";
var MESSAGES_TAB = "Messages";
var MAX_FIELD = 5000;
var MAX_MESSAGE = 20000;

// Run once from the Apps Script editor. It asks for permission and builds the tabs.
function setup() {
  var book = SpreadsheetApp.getActive();
  var clients = book.getSheetByName(CLIENTS_TAB) || book.insertSheet(CLIENTS_TAB);
  if (clients.getLastRow() === 0) {
    clients.appendRow(["Site ID", "Send to", "Business name"]);
    clients.appendRow(["clarks-boxing", "clarksboxinggym@gmail.com", "Clark's Boxing Club"]);
  }
  var messages = book.getSheetByName(MESSAGES_TAB) || book.insertSheet(MESSAGES_TAB);
  if (messages.getLastRow() === 0) {
    messages.appendRow(["Received", "Business", "Subject", "Message"]);
  }
  Logger.log("Emails left today: " + MailApp.getRemainingDailyQuota());
}

// A quick check that the mailer is up. It sends nothing.
function doGet() {
  return reply({ ok: true });
}

function doPost(e) {
  try {
    var form = e.parameter;

    // The hidden honeypot field is only filled in by bots. Look successful, send nothing.
    if (form._gotcha) return reply({ ok: true });

    var client = findClient(form._site);
    if (!client) return reply({ ok: false, error: "unknown_site" });

    var subject = clip(form.subject || "New website message", 200).replace(/[\r\n]+/g, " ");
    var message = messageText(form);

    // Save first, so the message is kept even if the email fails.
    saveCopy(client, subject, message);

    var email = { to: client.email, subject: subject, body: message, name: client.name + " Website" };
    if (isEmail(form.email)) email.replyTo = form.email;
    MailApp.sendEmail(email);

    return reply({ ok: true });
  } catch (err) {
    console.error(err);
    return reply({ ok: false, error: "send_failed" });
  }
}

function findClient(siteId) {
  if (!siteId) return null;
  var rows = SpreadsheetApp.getActive().getSheetByName(CLIENTS_TAB).getDataRange().getValues();
  for (var i = 1; i < rows.length; i++) {
    if (String(rows[i][0]).trim() === siteId && rows[i][1]) {
      return { email: String(rows[i][1]).trim(), name: String(rows[i][2] || siteId).trim() };
    }
  }
  return null;
}

// Every visible form field, one per line. Names starting with _ are for this script.
function messageText(form) {
  var lines = Object.keys(form)
    .filter(function (key) { return key.charAt(0) !== "_" && key !== "subject"; })
    .map(function (key) { return key + ": " + clip(form[key], MAX_FIELD); });
  return clip(lines.join("\n"), MAX_MESSAGE);
}

// The leading ' makes Sheets treat visitor text as plain text, never as a formula.
function saveCopy(client, subject, message) {
  SpreadsheetApp.getActive().getSheetByName(MESSAGES_TAB)
    .appendRow([new Date(), "'" + client.name, "'" + subject, "'" + message]);
}

function isEmail(value) {
  return /^[^\s@,;<>]+@[^\s@,;<>]+\.[^\s@,;<>]+$/.test(value || "");
}

function clip(value, max) {
  return String(value).slice(0, max);
}

function reply(result) {
  return ContentService.createTextOutput(JSON.stringify(result))
    .setMimeType(ContentService.MimeType.JSON);
}
