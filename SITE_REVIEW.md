# QMA Site Review Checklist

Review the following pages and features. Give feedback using **one fix prompt** format.

## Pages Live

### Homepage
- [ ] `index.html` — Gemini video featured, quick form, chat widget, nav menu

### Service Pages (11 total — all with 15s commercial video)
- [ ] `roofing.html` — Video + form + "How it works"
- [ ] `hvac.html` — Video + form + "How it works"
- [ ] `plumbing.html` — Video + form
- [ ] `solar.html` — Video + form
- [ ] `lawn-care.html` — Video + form
- [ ] `painting.html` — Video + form
- [ ] `electrical.html` — Video + form
- [ ] `pest-control.html` — Video + form
- [ ] `tree-service.html` — Video + form
- [ ] `moving.html` — Video + form
- [ ] `house-cleaning.html` — Video + form

### Calculator Tools (5 total)
- [ ] `roof-calculator.html` — Slider + savings estimate
- [ ] `hvac-calculator.html` — Enhanced UI, Gemini promo, calculator
- [ ] `solar-calculator.html` — Enhanced UI, Gemini promo, calculator
- [ ] `moving-estimator.html` — Enhanced UI, Gemini promo, estimator
- [ ] `electrical-estimator.html` — Quick estimate tool
- [ ] `painting-calculator.html` — Quick estimate tool

### Business Pages
- [ ] `for-pros.html` — Contractor dashboard stub (sign-up CTA)
- [ ] `business-insurance.html` — Affiliate landing page (30-40% commission)
- [ ] `car-ai-guide.html` — AiMax affiliate (secondary)

### Legal Pages
- [ ] `privacy.html` — Privacy policy
- [ ] `terms.html` — Terms of service
- [ ] `disclaimer.html` — Disclaimer

## Features to Verify

### Lead Capture
- [ ] All forms post to Formspree (xpwzgqkd)
- [ ] TCPA consent line visible on every form
- [ ] "Reply STOP to unsubscribe" text present
- [ ] Forms mobile-responsive

### Chat Widget
- [ ] Green bubble visible (bottom-right)
- [ ] Pops up on click
- [ ] Answers: "Is it free?", "How long?", "Is it safe?"
- [ ] Routes to correct service pages
- [ ] Can be dismissed

### Video Embeds
- [ ] 15s commercial plays on all service pages (before form)
- [ ] Video controls (play/pause/mute)
- [ ] Mobile-friendly player

### Navigation
- [ ] Nav bar on every subpage
- [ ] Hamburger menu works on mobile
- [ ] Links to homepage, all services, calculators, legal

### Mobile Experience
- [ ] All pages responsive (test at 375px width)
- [ ] Forms stack vertically
- [ ] Video scales properly
- [ ] No horizontal scroll

### Branding
- [ ] Dark theme (#0f172a background)
- [ ] Emerald accent (#10b981) on buttons/links
- [ ] "Free Quotes On Anything!™" slogan visible
- [ ] QMA logo/brand consistent

## What to Test

1. **Form submission** — Fill out roofing quote form, submit
   - Verify confirmation message appears
   - Check Formspree email receipt

2. **Chat widget** — Click bubble, ask "is it free?"
   - Verify answer appears
   - Click "roof" link, should go to roofing.html

3. **Calculator** — Try HVAC or solar calculator
   - Adjust inputs, see results update
   - Click "Get Free HVAC Quotes" link

4. **Video** — Play 15s commercial on 2-3 service pages
   - Verify audio works
   - Test on mobile

5. **Navigation** — Go to 3 different service pages
   - Verify hamburger menu works
   - Click links back to homepage

## Feedback Format

When you review, give **ONE fix prompt** in this format:

```
FIXES:
- [Issue 1]: [what to change]
- [Issue 2]: [what to change]
- [Issue 3]: [what to change]
```

Example:
```
FIXES:
- Roofing video not playing on mobile
- Missing privacy link in footer
- Chat widget positioning overlaps form on iPhone
```

Then we fix + commit + push → **LIVE**

---

**Status:** All 25+ pages built, tested locally. Ready for your review.
