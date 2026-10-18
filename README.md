# Clark's Boxing Club website

Plain HTML/CSS/JS with no build step. It can be hosted anywhere that serves static files (Netlify, Cloudflare Pages, GitHub Pages).

| Page | File |
| --- | --- |
| Home | `index.html` |
| Training | `training.html` |
| Plans & Pricing + Box-Fit Nutrition | `pricing.html` |
| Coach Clark (story + videos) | `about.html` |
| Free trial / contact form | `contact.html` |

Styles live in `css/styles.css`, and the menu and form logic live in `js/main.js`. Photos are in `images/`. They come from the old Wix site and the gym's public Facebook page.

## Preview locally

```bash
python3 -m http.server 8800 --directory .
```

Then open http://127.0.0.1:8800.

## Editing

The header and footer are repeated in every page. If you change the phone number, hours or menu, update all five `.html` files.

## Contact form

The form sends to clarksboxinggym@gmail.com through [FormSubmit](https://formsubmit.co). The **first** time someone submits it, FormSubmit sends an activation email to that inbox. Someone must click the link in it before messages start arriving.
