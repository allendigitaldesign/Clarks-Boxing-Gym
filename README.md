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

The form sends to clarksboxinggym@gmail.com through [Formspree](https://formspree.io) on its free plan. The address is set on the Formspree form, not in this site's code. `contact.html` only holds the form's ID, in the `action` address of the `<form>` tag.

- **Free limit:** 50 messages a month. Past that, Formspree keeps new messages in the dashboard's Over Limit folder instead of emailing them, and sends a warning email first.
- **Backup copy:** Messages stay in the Formspree dashboard for 30 days, so a missed email isn't a lost lead.
- **If the service is down:** Visitors see the error message with the gym's phone number and email. Check [status.formspree.io](https://status.formspree.io).
- **Spam:** The hidden `_gotcha` field is the honeypot. Formspree silently ignores any submission that fills it in.
- **Analytics:** `js/main.js` sends a `contact_form_result` event with worked or failed, the two fixed choices, and a status number. It never includes what the visitor typed.
- **Testing:** Every real submission emails the gym, so check with Joseph before sending one.
