# scripts_gen_cities.py - Generate city landing pages for QuoteMyAnything
import os

# Top US cities example - expand to 510 as needed
cities = ["Austin TX", "Liberty Hill TX", "Round Rock TX", "Leander TX", "Georgetown TX"]  # placeholder, expand

services = ["roofing", "hvac", "plumbing", "cleaning", "landscaping", "painting"]

for city in cities:
    slug = city.lower().replace(" ", "-")
    content = f"""<!DOCTYPE html>
<html>
<head><title>Quote My Anything - {city}</title></head>
<body>
<h1>Get Quotes in {city}</h1>
<p>We connect you with local pros in {city} — we don’t do the work.</p>
<form id="quick-form">
<input type="hidden" name="source" value="qma-city-{slug}">
<!-- service selector etc. -->
</form>
</body>
</html>"""
    with open(f"qma-city-{slug}.html", "w") as f:
        f.write(content)

print("Generated city pages")