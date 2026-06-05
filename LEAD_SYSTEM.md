# Lead Capture & Routing System

## Current Setup
- **Form capture:** Formspree (free tier)
  - Service requests: xpwzgqkd
  - Main form: xdajvlvr
- **Workflow:** Formspree → email → Zapier → contractor routing

## Step 1: Zapier Workflow (connect Formspree)

### Trigger: New Formspree Submission
1. Go to zapier.com
2. Create Zap: "Formspree → Lead Router"
3. Trigger: Formspree → New Email → Select form (xpwzgqkd)
4. Trigger fields: name, email, phone, zip, service_details

### Action 1: Store in Google Sheets (lead log)
- Create Sheet: "QMA_Leads"
- Columns: timestamp, service, zip, email, phone, status (new/contacted/won/lost)
- Append each lead

### Action 2: Send alert email
- To: leads@quotemyanything.com
- Subject: [Service] Lead from [ZIP] - [Name]
- Body: Include all lead details + direct link to for-pros dashboard

### Action 3: Route by service/ZIP
- Condition: if service = roofing AND zip = 78704
- Send SMS or email to matched contractors (stored in contractor database)

## Step 2: Contractor Database (Google Sheet)

Create sheet: "Contractors"
Columns:
- Name
- Service (roofing, hvac, plumbing, etc.)
- Service ZIPs (78704, 78703, 78702, etc.)
- Contact email
- Contact phone
- Plan type (per-lead or monthly)
- Active (yes/no)

## Step 3: Lead Routing Logic

For each new lead:
1. Extract service + ZIP
2. Look up active contractors in that service + ZIP
3. If only 1 contractor: send lead (auto-assign)
4. If 2+ contractors: distribute round-robin
5. If none: hold lead, email admin

## Step 4: Contractor Dashboard (for-pros.html enhanced)

Future: Add login to view:
- Assigned leads
- Quote history
- Monthly usage
- Payment status

For now: Manual email loop

## Revenue Tracking

Sheet: "Revenue"
- Date, contractor, service, ZIP, amount (lead fee or monthly), payment status
- Monthly total MRR

## KPIs to Track

1. **Leads by service:** COUNTIF(service)
2. **Leads by ZIP:** COUNTIF(zip)
3. **Lead-to-quote rate:** (quotes sent) / (leads assigned)
4. **CAC by channel:** organic leads cost ~$0, free-trial ads = ad spend / leads
5. **Contractor retention:** active contractors / total signed

## Automation Enhancements (later)

- Stripe payment processing (per-lead charges)
- SMS notifications (Twilio)
- Auto-response emails to homeowners
- Contractor performance scoring
- Lead quality feedback loop

## Current Manual Workflow

Until Zapier is live:
1. New lead email arrives (from Formspree)
2. Copy to Google Sheet manually
3. Send to matching contractor(s) via email
4. Log response/outcome

Once Zapier live: fully automated.
