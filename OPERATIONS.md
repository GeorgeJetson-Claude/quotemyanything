# Daily Operations Setup

## Quick Start

### Manual Daily Run
```bash
cd quotemyanything-social/agents
python3 daily_workflow.py --service roofing
```

Output:
- ✓ Leads found and routed
- ✓ Draft replies generated
- ✓ Checklist of 15-min daily tasks
- ✓ Results logged to `leads_log.jsonl`

### Add to Cron (automatic daily runs)

#### Option 1: Morning run (8 AM)
```bash
crontab -e
# Add:
0 8 * * * cd /home/user/QMA/quotemyanything-social/agents && python3 daily_workflow.py --service roofing >> /tmp/qma_daily.log 2>&1
```

#### Option 2: Multiple services (daily)
```bash
0 8 * * * cd /home/user/QMA/quotemyanything-social/agents && for service in roofing hvac plumbing solar; do python3 daily_workflow.py --service $service; done
```

#### Option 3: Twice daily (8 AM + 4 PM)
```bash
0 8,16 * * * cd /home/user/QMA/quotemyanything-social/agents && python3 daily_workflow.py --service roofing
```

Check logs:
```bash
tail -f /tmp/qma_daily.log
```

## Lead Routing Setup

### 1. Add Contractors to lead_router.py

Edit `CONTRACTOR_DB` in `lead_router.py`:
```python
"roofing": [
    {"name": "Austin Roofing Pro", "zip": ["78704", "78703"], "email": "quotes@austinroofing.local"},
    {"name": "Central TX Roofing", "zip": ["78701", "78704"], "email": "leads@centraltxroofing.local"},
],
```

### 2. Zapier Setup (semi-automated)

1. **Trigger:** Formspree new submission
2. **Actions:**
   - Log to Google Sheets (QMA_Leads)
   - Send email alert to leads@quotemyanything.com
   - (Optional) SMS to assigned contractor via Twilio

### 3. Manual Lead Follow-up (current workflow)

Until Zapier is live:
```
New lead from Formspree → 
  Copy to Google Sheet → 
  Match to contractor(s) → 
  Email contractor with lead
```

## Google Sheets Setup

Create two sheets:

### Sheet 1: QMA_Leads
Columns: timestamp, name, email, phone, zip, service, status (new/contacted/quoted/won/lost)

### Sheet 2: Contractors
Columns: name, service, zips (comma-separated), email, phone, plan_type (per-lead/monthly), active (yes/no)

Share read-only link to contractors.

## Revenue Tracking

Track in Google Sheet:
- Date
- Contractor
- Service
- Lead count
- Revenue (lead fee or monthly subscription)
- Payment status

Monthly recurring revenue (MRR) = sum of all active monthly subscriptions.

## Metrics to Track Daily

1. **Leads captured:** Count in Formspree
2. **Leads routed:** Successful matches to contractors
3. **Quotes sent:** Contractor responses
4. **Win rate:** Completed jobs / leads assigned
5. **MRR:** Sum of active contractor subscriptions

## Weekly Checklist

- [ ] Run daily_workflow.py 5+ times (or set cron)
- [ ] Review organic leads found (Reddit/Discord)
- [ ] Email new leads to contractors
- [ ] Log responses/quotes in sheet
- [ ] Update contractor database (add/remove as needed)
- [ ] Update revenue tracker
- [ ] Calculate weekly MRR

## Monthly Checklist

- [ ] Review lead volume by service
- [ ] Review contractor retention
- [ ] Calculate customer acquisition cost (CAC)
- [ ] Identify high-intent keywords for ads
- [ ] Plan next city launch (Houston, Dallas, etc.)

## Next Automation Goals

1. **Stripe payment processing** - automate per-lead charges
2. **SMS notifications** - alert contractors of new leads
3. **Contractor portal** - self-serve lead assignment
4. **Lead quality scoring** - rank leads by intent
5. **Auto-response emails** - confirm receipt to homeowner

## Troubleshooting

### No leads found
- Check subreddit availability
- Verify keywords in channels.json
- Check Reddit rate limits

### Leads not routing
- Verify contractor ZIPs in lead_router.py
- Check service mapping in SERVICE_MAP
- Test with manual lead

### Zapier not triggering
- Verify Formspree form ID is correct
- Check Zapier task history
- Manually test form submission

---

**Production launch ready: YES** (once Zapier + payment processing online)
