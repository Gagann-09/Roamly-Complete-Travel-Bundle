C = ("culture", "food", "nature", "adventure", "relax", "nightlife")
TIERS = {"budget": dict(stay=1500, food=600, move=500), "mid": dict(stay=4000, food=1400, move=1200), "luxury": dict(stay=12000, food=3500, move=3000)}
# activity: (name, category, cost_per_person_INR, hours, slot m/a/e, lat, lng, description). Costs and coordinates are approximate.
DEST = {
"goa": dict(name="Goa", mult=1.1, best="Nov–Feb", climate="Hot and humid. Monsoon (Jun–Sep) closes many beach shacks.", lat=15.50, lng=73.83, acts=[
 ("Old Goa churches & Basilica of Bom Jesus","culture",0,2,"m",15.5009,73.9116,"UNESCO-listed Baroque churches."),
 ("Dudhsagar Falls jeep safari","adventure",1500,5,"m",15.3144,74.3143,"Jeep ride to a four-tier waterfall."),
 ("Fontainhas Latin Quarter walk","culture",0,2,"a",15.4969,73.8313,"Painted Portuguese-era lanes in Panjim."),
 ("Goan fish-thali lunch in Panjim","food",600,1.5,"a",15.4909,73.8278,"Recheado fish, xacuti and sol kadi."),
 ("Baga water sports","adventure",1200,2,"a",15.5553,73.7517,"Parasailing and jet-ski."),
 ("Palolem Beach sunset","relax",0,3,"e",15.0100,74.0232,"Calm crescent beach."),
 ("Chapora Fort sunset","nature",0,2,"e",15.6068,73.7366,"Hilltop fort with sea views."),
 ("Vagator beach-club night","nightlife",1500,3,"e",15.6000,73.7400,"Music and sunset cocktails.")]),
"jaipur": dict(name="Jaipur", mult=0.9, best="Oct–Mar", climate="Very hot Apr–Jun. Winter days are mild and clear.", lat=26.92, lng=75.82, acts=[
 ("Amber Fort tour","culture",500,3,"m",26.9855,75.8513,"Hilltop fort-palace with mirror work."),
 ("City Palace & Jantar Mantar","culture",700,3,"m",26.9258,75.8236,"Royal palace and 18th-century observatory."),
 ("Sunrise hot-air balloon ride","adventure",12000,2,"m",26.9900,75.8500,"Dawn flight over forts and fields."),
 ("Hawa Mahal & Johari Bazaar","culture",200,2,"a",26.9239,75.8267,"Pink facade and jewellery bazaar."),
 ("Rajasthani thali & lassi crawl","food",700,2,"a",26.9196,75.8190,"Dal baati churma in the old city."),
 ("Nahargarh Fort sunset","nature",100,2,"e",26.9373,75.8155,"City views from the ridge."),
 ("Chokhi Dhani village dinner","nightlife",1200,3,"e",26.7728,75.8458,"Folk dance and a Rajasthani dinner."),
 ("Jal Mahal lakeside stroll","relax",0,1.5,"e",26.9535,75.8460,"Quiet photo stop on Man Sagar Lake.")]),
"munnar": dict(name="Munnar (Kerala)", mult=1.0, best="Sep–Mar", climate="Cool and misty. Heavy rain Jun–Aug.", lat=10.09, lng=77.06, acts=[
 ("Eravikulam National Park","nature",300,3,"m",10.2000,77.0600,"Nilgiri tahr and grassland views."),
 ("Kolukkumalai sunrise jeep ride","adventure",2000,4,"m",10.0722,77.2400,"High-altitude tea estate at dawn."),
 ("Tea Museum & plantation walk","culture",300,2,"a",10.0875,77.0618,"History of Munnar tea."),
 ("Mattupetty Dam boating","relax",400,1.5,"a",10.1065,77.1227,"Lake boating near Echo Point."),
 ("Kerala sadya lunch","food",500,1.5,"a",10.0889,77.0595,"Banana-leaf vegetarian feast."),
 ("Attukal waterfalls trek","adventure",100,2,"a",10.0467,77.0128,"Short forest trail to falls."),
 ("Kathakali & Kalaripayattu show","culture",350,1.5,"e",10.0850,77.0600,"Traditional Kerala performance."),
 ("Plantation campfire & stargazing","relax",800,2.5,"e",10.0900,77.0700,"Quiet evening at a hill stay.")]),
"rishikesh": dict(name="Rishikesh", mult=0.8, best="Sep–Nov, Feb–Apr", climate="Hot in summer. Rafting closes in monsoon (Jul–Sep).", lat=30.09, lng=78.29, acts=[
 ("White-water rafting (16 km)","adventure",1500,4,"m",30.1160,78.3350,"Grade 2–3 rapids on the Ganga."),
 ("Yoga & meditation session","relax",500,1.5,"m",30.1100,78.3050,"Morning class at a riverside ashram."),
 ("Neer Garh waterfall hike","nature",100,3,"m",30.1332,78.3360,"Forest trail with pools."),
 ("Laxman & Ram Jhula walk","culture",0,2,"a",30.1269,78.3239,"Iconic suspension bridges."),
 ("Beatles Ashram visit","culture",150,2,"a",30.1050,78.3130,"Abandoned ashram with street art."),
 ("Cafe-hopping on the Ganga","food",600,2,"a",30.1250,78.3260,"Riverside cafes and bakeries."),
 ("Ganga Aarti at Triveni Ghat","culture",0,1.5,"e",30.1010,78.2970,"Evening lamp ceremony."),
 ("Parmarth Niketan ghat sunset","relax",0,2,"e",30.1210,78.3270,"Quiet sunset by the river.")]),
"hampi": dict(name="Hampi", mult=0.8, best="Oct–Feb", climate="Dry and very hot Mar–May. Winter is best.", lat=15.335, lng=76.46, acts=[
 ("Virupaksha Temple & Hampi Bazaar","culture",50,2,"m",15.3350,76.4600,"Living 7th-century temple."),
 ("Vittala Temple & Stone Chariot","culture",40,2.5,"m",15.3430,76.4750,"Musical pillars and the iconic chariot."),
 ("Matanga Hill sunrise climb","nature",0,2,"m",15.3300,76.4700,"Short climb with 360° views."),
 ("Lotus Mahal & Elephant Stables","culture",40,2,"a",15.3260,76.4690,"Royal enclosure monuments."),
 ("Coracle ride on the Tungabhadra","adventure",300,1.5,"a",15.3300,76.4660,"Round boat across the river."),
 ("Cafe lunch in Virupapur Gadde","food",500,1.5,"a",15.3420,76.4650,"Relaxed cafes across the river."),
 ("Hemakuta Hill sunset","nature",0,2,"e",15.3330,76.4590,"Temple ruins and golden light."),
 ("Riverside cafe music night","nightlife",600,2,"e",15.3400,76.4580,"Live acoustic sets.")]),
}
