#!/usr/bin/env python3
"""Generate QMA city landing pages for top US cities."""
import os, re, pathlib

CITIES = """New York,NY|Los Angeles,CA|Chicago,IL|Houston,TX|Phoenix,AZ|Philadelphia,PA|San Antonio,TX|San Diego,CA|Dallas,TX|Jacksonville,FL|Austin,TX|Fort Worth,TX|San Jose,CA|Columbus,OH|Charlotte,NC|Indianapolis,IN|San Francisco,CA|Seattle,WA|Denver,CO|Washington,DC|Nashville,TN|Oklahoma City,OK|El Paso,TX|Boston,MA|Portland,OR|Las Vegas,NV|Detroit,MI|Memphis,TN|Louisville,KY|Baltimore,MD|Milwaukee,WI|Albuquerque,NM|Tucson,AZ|Fresno,CA|Sacramento,CA|Mesa,AZ|Kansas City,MO|Atlanta,GA|Omaha,NE|Colorado Springs,CO|Raleigh,NC|Long Beach,CA|Virginia Beach,VA|Miami,FL|Oakland,CA|Minneapolis,MN|Tulsa,OK|Bakersfield,CA|Wichita,KS|Arlington,TX|Aurora,CO|Tampa,FL|New Orleans,LA|Cleveland,OH|Honolulu,HI|Anaheim,CA|Lexington,KY|Stockton,CA|Corpus Christi,TX|Henderson,NV|Riverside,CA|Newark,NJ|Saint Paul,MN|Santa Ana,CA|Cincinnati,OH|Irvine,CA|Orlando,FL|Pittsburgh,PA|St. Louis,MO|Greensboro,NC|Jersey City,NJ|Anchorage,AK|Lincoln,NE|Plano,TX|Durham,NC|Buffalo,NY|Chandler,AZ|Chula Vista,CA|Toledo,OH|Madison,WI|Gilbert,AZ|Reno,NV|Fort Wayne,IN|North Las Vegas,NV|St. Petersburg,FL|Lubbock,TX|Irving,TX|Laredo,TX|Winston-Salem,NC|Chesapeake,VA|Glendale,AZ|Garland,TX|Scottsdale,AZ|Norfolk,VA|Boise,ID|Fremont,CA|Spokane,WA|Santa Clarita,CA|Baton Rouge,LA|Richmond,VA|Hialeah,FL|San Bernardino,CA|Tacoma,WA|Modesto,CA|Huntsville,AL|Des Moines,IA|Yonkers,NY|Rochester,NY|Moreno Valley,CA|Fayetteville,NC|Fontana,CA|Columbus,GA|Worcester,MA|Port St. Lucie,FL|Little Rock,AR|Augusta,GA|Oxnard,CA|Birmingham,AL|Montgomery,AL|Frisco,TX|Amarillo,TX|Salt Lake City,UT|Grand Rapids,MI|Huntington Beach,CA|Overland Park,KS|Glendale,CA|Tallahassee,FL|Grand Prairie,TX|McKinney,TX|Cape Coral,FL|Sioux Falls,SD|Peoria,AZ|Providence,RI|Vancouver,WA|Knoxville,TN|Akron,OH|Shreveport,LA|Mobile,AL|Brownsville,TX|Newport News,VA|Fort Lauderdale,FL|Chattanooga,TN|Tempe,AZ|Aurora,IL|Santa Rosa,CA|Eugene,OR|Elk Grove,CA|Salem,OR|Ontario,CA|Cary,NC|Rancho Cucamonga,CA|Oceanside,CA|Lancaster,CA|Garden Grove,CA|Pembroke Pines,FL|Fort Collins,CO|Palmdale,CA|Springfield,MO|Clarksville,TN|Salinas,CA|Hayward,CA|Paterson,NJ|Alexandria,VA|Macon,GA|Corona,CA|Kansas City,KS|Lakewood,CO|Springfield,MA|Sunnyvale,CA|Jackson,MS|Killeen,TX|Hollywood,FL|Pasadena,TX|Pomona,CA|Escondido,CA|Charleston,SC|Rockford,IL|Joliet,IL|Bellevue,WA|Naperville,IL|Roseville,CA|Bridgeport,CT|Mesquite,TX|Savannah,GA|Syracuse,NY|McAllen,TX|Pasadena,CA|Denton,TX|Surprise,AZ|Carrollton,TX|Torrance,CA|Olathe,KS|Visalia,CA|Thornton,CO|Fullerton,CA|Gainesville,FL|Waco,TX|West Valley City,UT|Warren,MI|Lakewood,NJ|Hampton,VA|Dayton,OH|Columbia,SC|Orange,CA|Cedar Rapids,IA|Stamford,CT|Victorville,CA|Pearland,TX|Elizabeth,NJ|Coral Springs,FL|Round Rock,TX|Sterling Heights,MI|Kent,WA|Columbia,MO|Santa Clara,CA|New Haven,CT|Athens,GA|Thousand Oaks,CA|Lafayette,LA|Simi Valley,CA|Topeka,KS|Norman,OK|Fargo,ND|Wilmington,NC|Abilene,TX|Odessa,TX|Concord,CA|Hartford,CT|Berkeley,CA|North Charleston,SC|Vallejo,CA|Allentown,PA|Rochester,MN|Arvada,CO|Ann Arbor,MI|Cambridge,MA|Sugar Land,TX|Lansing,MI|Evansville,IN|College Station,TX|Fairfield,CA|Clearwater,FL|Beaumont,TX|Independence,MO|Provo,UT|West Jordan,UT|Murfreesboro,TN|El Monte,CA|Carlsbad,CA|North Charleston,SC|Temecula,CA|Clovis,CA|Springfield,IL|Meridian,ID|Westminster,CO|Costa Mesa,CA|High Point,NC|Manchester,NH|Pueblo,CO|Lakeland,FL|Pompano Beach,FL|West Palm Beach,FL|Antioch,CA|Everett,WA|Downey,CA|Lowell,MA|Centennial,CO|Elgin,IL|Richardson,TX|Gresham,OR|Inglewood,CA|Broken Arrow,OK|Miami Gardens,FL|Billings,MT|Jurupa Valley,CA|Sandy Springs,GA|Hillsboro,OR|Waterbury,CT|Santa Maria,CA|Boulder,CO|Greeley,CO|Daly City,CA|Meridian,MS|Lewisville,TX|Davie,FL|West Covina,CA|League City,TX|Tyler,TX|Norwalk,CA|San Mateo,CA|Green Bay,WI|Wichita Falls,TX|Burbank,CA|Rialto,CA|Vista,CA|El Cajon,CA|Edinburg,TX|Davenport,IA|South Bend,IN|Renton,WA|Murrieta,CA|Woodbridge,NJ|Vacaville,CA|Spokane Valley,WA|Lakeland,FL|Quincy,MA|Erie,PA|Tuscaloosa,AL|Las Cruces,NM|Sparks,NV|Carrollton,GA|San Marcos,CA|Hesperia,CA|North Port,FL|Mission Viejo,CA|Olympia,WA|Fishers,IN|Concord,NC|Westland,MI|Bend,OR|Carmel,IN|Clinton,MI|Tracy,CA|Bryan,TX|Lynn,MA|Norman,OK|Apple Valley,CA|Buckeye,AZ|Goodyear,AZ|Edmond,OK|Federal Way,WA|Sandy,UT|Springdale,AR|Yuma,AZ|Ogden,UT|Tustin,CA|Roanoke,VA|Champaign,IL|Tuscaloosa,AL|Greenville,NC|Lawton,OK|Suffolk,VA|Bloomington,MN|San Angelo,TX|Newton,MA|Decatur,IL|Pawtucket,RI|Boca Raton,FL|Lehi,UT|Hawthorne,CA|Whittier,CA|Newport Beach,CA|Brockton,MA|Sunrise,FL|Plantation,FL|Indio,CA|Camden,NJ|Trenton,NJ|Brooklyn Park,MN|Ogden,UT|Sioux City,IA|Idaho Falls,ID|Lawrence,KS|Fayetteville,AR|Reading,PA|Yakima,WA|Lake Forest,CA|Compton,CA|Citrus Heights,CA|Livonia,MI|Tracy,CA|Alhambra,CA|Kirkland,WA|Trenton,NJ|Ocala,FL|Tamarac,FL|Hemet,CA|Chico,CA|Nampa,ID|Eagan,MN|Auburn,WA|Redwood City,CA|Lake Charles,LA|Bloomington,IL|Pharr,TX|Appleton,WI|Gastonia,NC|Folsom,CA|Southfield,MI|Rochester Hills,MI|New Bedford,MA|Jonesboro,AR|Bellingham,WA|Schaumburg,IL|Mountain View,CA|Pleasanton,CA|Union City,CA|Auburn,AL|Decatur,AL|Redding,CA|Lakewood,CA|Merced,CA|Bossier City,LA|Albany,NY|Largo,FL|Santa Monica,CA|Bowling Green,KY|Council Bluffs,IA|Bristol,CT|Lynchburg,VA|Conroe,TX|Missouri City,TX|Frederick,MD|Waukegan,IL|Bayonne,NJ|Round Lake Beach,IL|Jackson,TN|Sammamish,WA|Brentwood,CA|Newark,OH|Plymouth,MN|Joplin,MO|Champaign,IL|Marysville,WA|Vineland,NJ|Macon,GA|Salem,MA|Sammamish,WA|Greenwood,IN|Castle Rock,CO|Carson City,NV|Tigard,OR|Cathedral City,CA|Pawtucket,RI|Encinitas,CA|Hattiesburg,MS|Edmond,OK|Bartlett,TN|Pittsfield,MA|Saint Joseph,MO|Rocklin,CA|San Luis Obispo,CA|Beavercreek,OH|Wylie,TX|Casper,WY|Bowie,MD|Apex,NC|Schenectady,NY|Maple Grove,MN|Highlands Ranch,CO|Bethlehem,PA|Lake Havasu City,AZ|Quincy,IL|Eau Claire,WI|Camarillo,CA|Yuba City,CA|Avondale,AZ|Conway,AR|Caldwell,ID|Cuyahoga Falls,OH|Lawrence,MA|Wheaton,IL|Coon Rapids,MN|Mount Pleasant,SC|Bryan,TX|Springfield,OH|Pico Rivera,CA|San Clemente,CA|Beaverton,OR|Madera,CA|San Rafael,CA|Davis,CA|Yorba Linda,CA|Bismarck,ND|Bell Gardens,CA|Coeur d'Alene,ID|Lompoc,CA|North Richland Hills,TX|Tinley Park,IL|Doral,FL|Yucaipa,CA|Walnut Creek,CA|Mansfield,TX|Bountiful,UT|Hanford,CA|Madison,AL|Margate,FL|Petaluma,CA|Aspen Hill,MD|Fountain Valley,CA|Diamond Bar,CA|Suffolk,VA|Carson,CA|Hoover,AL|Santa Fe,NM|Rocky Mount,NC|Burnsville,MN|Burien,WA|Eden Prairie,MN|Skokie,IL|Manhattan,KS|Springfield,OR|Anderson,IN|Florissant,MO|Lehi,UT|Burlington,NC|Apopka,FL|Sanford,FL|Wausau,WI|Annapolis,MD|Brookhaven,GA|Dunwoody,GA|Smyrna,GA|Marietta,GA|Roswell,GA|Sandy Springs,GA|Albany,GA|Warner Robins,GA|Valdosta,GA|Statesboro,GA|Dalton,GA|Rome,GA|Hinesville,GA|Brunswick,GA|Gainesville,GA|Kennesaw,GA"""

cities = []
seen = set()
for entry in CITIES.split("|"):
    name, state = entry.split(",")
    key = (name.strip(), state.strip())
    if key in seen: continue
    seen.add(key)
    cities.append(key)

cities = cities[:550]
print(f"Generating {len(cities)} city pages")

SERVICES = [
    ("Roofing","roofing.html","Roof repair, replacement, inspection"),
    ("HVAC","hvac.html","Heating, AC, furnace install & repair"),
    ("Plumbing","plumbing.html","Leak repair, water heaters, drains"),
    ("Electrical","electrical.html","Panel upgrades, wiring, lighting"),
    ("Solar","solar.html","Solar panels & install quotes"),
    ("Painting","painting.html","Interior & exterior painters"),
    ("Lawn Care","lawn-care.html","Mowing, landscaping, sod"),
    ("Pest Control","pest-control.html","Termites, rodents, insects"),
    ("Tree Service","tree-service.html","Removal, trimming, stump grinding"),
    ("Moving","moving.html","Local & long-distance movers"),
    ("House Cleaning","house-cleaning.html","Move-in, deep clean, recurring"),
]

TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Free Quotes in {city}, {state} - Roofing, HVAC, Plumbing &amp; More | QuoteMyAnything</title>
<meta name="description" content="Get free competing quotes from licensed local pros in {city}, {state}. Roofing, HVAC, plumbing, electrical, solar, painting and more. 60-second form. No spam.">
<link rel="canonical" href="https://quotemyanything.com/qma-city-{slug}.html">
<meta name="robots" content="index,follow">
<script type="application/ld+json">{{"@context":"https://schema.org","@type":"LocalBusiness","name":"QuoteMyAnything - {city}","areaServed":{{"@type":"City","name":"{city}, {state}"}},"url":"https://quotemyanything.com/qma-city-{slug}.html","priceRange":"Free"}}</script>
<script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-zinc-950 text-zinc-100">
<nav class="border-b border-zinc-800 p-3 text-sm">
  <div class="max-w-3xl mx-auto flex items-center justify-between">
    <a href="index.html" class="font-bold flex items-center gap-2"><span class="inline-block w-5 h-5 bg-emerald-500 text-zinc-950 rounded text-center text-xs font-black leading-5">Q</span><span class="text-white">QMA</span></a>
    <a href="index.html#quick-form" class="text-emerald-400">Get Free Quotes</a>
  </div>
</nav>
<header class="px-5 py-12 text-center bg-gradient-to-b from-zinc-900 to-zinc-950">
  <div class="inline-block bg-emerald-500 text-zinc-950 text-xs font-bold px-3 py-1 rounded-full tracking-widest mb-4">FREE - NO SPAM - 60 SECONDS</div>
  <h1 class="text-3xl md:text-5xl font-extrabold leading-tight max-w-3xl mx-auto">Free Local Quotes in <span class="text-amber-400">{city}, {state}</span></h1>
  <p class="text-zinc-400 mt-4 max-w-xl mx-auto">Compare 3 licensed {city} pros side-by-side. Roofing, HVAC, plumbing, electrical, solar, painting, lawn, pest, tree, moving, cleaning. We never call you. Email only.</p>
  <a href="index.html#quick-form" class="inline-block mt-7 bg-amber-500 hover:bg-amber-400 text-zinc-950 font-bold px-7 py-3 rounded-xl">Get My Free Quotes</a>
</header>
<section class="max-w-3xl mx-auto px-5 py-10">
  <h2 class="text-xl font-bold mb-5">Services in {city}</h2>
  <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
    {service_cards}
  </div>
</section>
<section class="max-w-3xl mx-auto px-5 py-8 text-sm text-zinc-400">
  <h2 class="text-lg font-bold text-white mb-3">Why {city} homeowners use QuoteMyAnything</h2>
  <ul class="space-y-2 list-disc pl-5">
    <li>Licensed, insured pros serving {city}, {state} and surrounding areas</li>
    <li>Competitive bidding - local contractors compete for your job</li>
    <li>No phone calls. Quotes by email only. You stay in control.</li>
    <li>Free to use. We earn from pros, not from you.</li>
  </ul>
</section>
<footer class="text-center text-xs text-zinc-600 py-6 border-t border-zinc-900">
  <a href="index.html" class="text-zinc-500">Home</a> - <a href="for-pros.html" class="text-zinc-500">For Pros</a> - <a href="privacy.html" class="text-zinc-500">Privacy</a> - <a href="terms.html" class="text-zinc-500">Terms</a>
  <div class="mt-2">QuoteMyAnything - Serving {city}, {state}</div>
</footer>
</body>
</html>
"""

def slugify(name, state):
    s = f"{name}-{state}".lower()
    s = re.sub(r"[^a-z0-9]+","-", s).strip("-")
    return s

OUT = pathlib.Path("/tmp/qma-city-pages")
OUT.mkdir(exist_ok=True)

for name, state in cities:
    slug = slugify(name, state)
    cards = "\n    ".join(
        f'<a href="{href}" class="block bg-zinc-900 border border-zinc-800 rounded-xl p-4 hover:border-emerald-500 transition"><div class="font-bold text-white">{svc} in {name}</div><div class="text-xs text-zinc-400 mt-1">{desc}</div></a>'
        for svc, href, desc in SERVICES
    )
    html = TEMPLATE.format(city=name, state=state, slug=slug, service_cards=cards)
    (OUT / f"qma-city-{slug}.html").write_text(html)

idx_links = "\n".join(
    f'<li><a href="qma-city-{slugify(n,s)}.html">{n}, {s}</a></li>' for n,s in cities
)
(OUT / "qma-cities-index.html").write_text(f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><title>QMA City Index - {len(cities)} Cities</title><link rel="canonical" href="https://quotemyanything.com/qma-cities-index.html"></head><body><h1>QuoteMyAnything - Local Quotes in {len(cities)} Cities</h1><ul>{idx_links}</ul></body></html>""")

sm = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
for n,s in cities:
    sm += f"  <url><loc>https://quotemyanything.com/qma-city-{slugify(n,s)}.html</loc><changefreq>weekly</changefreq><priority>0.7</priority></url>\n"
sm += "</urlset>\n"
(OUT / "qma-cities-sitemap.xml").write_text(sm)

print(f"Wrote {len(list(OUT.glob('qma-city-*.html')))} pages to {OUT}")
