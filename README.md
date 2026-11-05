# Clark's Boxing Club website

Plain HTML/CSS/JS with no build step. It can be hosted anywhere that serves static files (Netlify, Cloudflare Pages, GitHub Pages).

| Page | File |
| --- | --- |
| Home | `index.html` |
| Training | `training.html` |
| Plans & Pricing + Box-Fit Nutrition | `pricing.html` |
| Coach Clark (story + videos) | `about.html` |
| Free trial / contact form | `contact.html` |

Styles live in `css/styles.css`, the menu and form logic live in `js/main.js`, and visitor analytics live in `js/analytics.js` (PostHog, live domain only). Photos are in `images/`. They come from the old Wix site and the gym's public Facebook page.

## Preview locally

```bash
python3 -m http.server 8800 --directory .
```

Then open http://127.0.0.1:8800.

## Editing

The header and footer are repeated in every page. If you change the phone number, hours or menu, update all five `.html` files.

## Contact form

The form sends to clarksboxinggym@gmail.com through a small free Google script that runs from Joseph's Google account. It needs no form service, and the gym doesn't need an account or a verification email. The script's code is in `google-form-mailer/Code.gs`, and it lives in a Google Sheet called "Website Form Messages". `contact.html` holds the script's web address in the `<form>` tag, plus this site's ID, `clarks-boxing`.

- **Where messages go:** The Sheet's Clients tab matches each site's ID to the inbox that gets its email. To add a client, add a row there and give that site's form the new ID. The same script serves every site.
- **Free limit:** 100 emails a day across all client sites, set by Google.
- **Sender:** Emails come from Joseph's Gmail, using the business's name. Replying goes to the visitor.
- **Backup copy:** Every message is saved in the Sheet's Messages tab before it's emailed, so a missed email isn't a lost lead. Those messages hold visitors' contact details and stay until someone deletes them.
- **If something fails:** Visitors see the error message with the gym's phone number and email.
- **Spam:** The hidden `_gotcha` field is the honeypot. The script ignores any submission that fills it in.
- **Analytics:** `js/main.js` sends a `contact_form_result` event with worked or failed, the two fixed choices, and a fixed error label. It never includes what the visitor typed.
- **Changing the script:** Code changes only go live after publishing a new version of the existing deployment, which keeps the same web address.
- **Testing:** Every real submission emails the gym, so check with Joseph before sending one.
