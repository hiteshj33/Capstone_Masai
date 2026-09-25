"""Offline fallback for raw_books.csv — used only if scrape.py can't reach
books.toscrape.com (e.g. a restricted network). Titles/prices/categories
below are real, fetched from the live site; star ratings are meaningless on
that site anyway (it says so itself), so they're a deterministic hash here.
Run: python seed_data.py
"""
import csv, hashlib

RATINGS = ["One", "Two", "Three", "Four", "Five"]

# title, price_gbp, availability, category
BOOKS = [
    ("Sharp Objects", "£47.82", "In stock", "Mystery"),
    ("In a Dark, Dark Wood", "£19.63", "In stock", "Mystery"),
    ("The Past Never Ends", "£56.50", "In stock", "Mystery"),
    ("A Murder in Time", "£16.64", "In stock", "Mystery"),
    ("The Murder of Roger Ackroyd (Hercule Poirot #4)", "£44.10", "In stock", "Mystery"),
    ("The Last Mile (Amos Decker #2)", "£54.21", "In stock", "Mystery"),
    ("That Darkness (Gardiner and Renner #1)", "£13.92", "In stock", "Mystery"),
    ("Tastes Like Fear (DI Marnie Rome #3)", "£10.69", "In stock", "Mystery"),
    ("A Time of Torment (Charlie Parker #14)", "£48.35", "In stock", "Mystery"),
    ("A Study in Scarlet (Sherlock Holmes #1)", "£16.73", "In stock", "Mystery"),
    ("Poisonous (Max Revere Novels #3)", "£26.80", "In stock", "Mystery"),
    ("Murder at the 42nd Street Library (Raymond Ambler #1)", "£54.36", "In stock", "Mystery"),
    ("Most Wanted", "£35.28", "In stock", "Mystery"),
    ("Hide Away (Eve Duncan #20)", "£11.84", "In stock", "Mystery"),
    ("Boar Island (Anna Pigeon #19)", "£59.48", "In stock", "Mystery"),
    ("The Widow", "£27.26", "In stock", "Mystery"),
    ("Playing with Fire", "£13.71", "In stock", "Mystery"),
    ("What Happened on Beale Street (Secrets of the South Mysteries #2)", "£25.37", "In stock", "Mystery"),
    ("The Bachelor Girl's Guide to Murder (Herringford and Watts Mysteries #1)", "£52.30", "In stock", "Mystery"),
    ("Delivering the Truth (Quaker Midwife Mystery #1)", "£20.89", "In stock", "Mystery"),
    ("The Mysterious Affair at Styles (Hercule Poirot #1)", "£24.80", "In stock", "Mystery"),
    ("In the Woods (Dublin Murder Squad #1)", "£38.38", "In stock", "Mystery"),
    ("The Silkworm (Cormoran Strike #2)", "£23.05", "In stock", "Mystery"),
    ("The Exiled", "£43.45", "In stock", "Mystery"),
    ("The Cuckoo's Calling (Cormoran Strike #1)", "£19.21", "In stock", "Mystery"),
    ("Extreme Prey (Lucas Davenport #26)", "£25.40", "In stock", "Mystery"),
    ("Career of Evil (Cormoran Strike #3)", "£24.72", "In stock", "Mystery"),
    ("The No. 1 Ladies' Detective Agency (No. 1 Ladies' Detective Agency #1)", "£57.70", "In stock", "Mystery"),
    ("The Girl You Lost", "£12.29", "In stock", "Mystery"),
    ("The Girl In The Ice (DCI Erika Foster #1)", "£15.85", "In stock", "Mystery"),
    ("Blood Defense (Samantha Brinkman #1)", "£20.30", "In stock", "Mystery"),
    ("1st to Die (Women's Murder Club #1)", "£53.98", "In stock", "Mystery"),
    ("It's Only the Himalayas", "£45.17", "In stock", "Travel"),
    ("Full Moon over Noah's Ark: An Odyssey to Mount Ararat and Beyond", "£49.43", "In stock", "Travel"),
    ("See America: A Celebration of Our National Parks & Treasured Sites", "£48.87", "In stock", "Travel"),
    ("Vagabonding: An Uncommon Guide to the Art of Long-Term World Travel", "£36.94", "In stock", "Travel"),
    ("Under the Tuscan Sun", "£37.33", "In stock", "Travel"),
    ("A Summer In Europe", "£44.34", "In stock", "Travel"),
    ("The Great Railway Bazaar", "£30.54", "In stock", "Travel"),
    ("A Year in Provence (Provence #1)", "£56.88", "In stock", "Travel"),
    ("The Road to Little Dribbling: Adventures of an American in Britain (Notes From a Small Island #2)", "£23.21", "In stock", "Travel"),
    ("Neither Here nor There: Travels in Europe", "£38.95", "In stock", "Travel"),
    ("1,000 Places to See Before You Die", "£26.08", "In stock", "Travel"),
    ("Tipping the Velvet", "£53.74", "In stock", "Historical Fiction"),
    ("Forever and Forever: The Courtship of Henry Longfellow and Fanny Appleton", "£29.69", "In stock", "Historical Fiction"),
    ("A Flight of Arrows (The Pathfinders #2)", "£55.53", "In stock", "Historical Fiction"),
    ("The House by the Lake", "£36.95", "In stock", "Historical Fiction"),
    ("Mrs. Houdini", "£30.25", "In stock", "Historical Fiction"),
    ("The Marriage of Opposites", "£28.08", "In stock", "Historical Fiction"),
    ("Glory over Everything: Beyond The Kitchen House", "£45.84", "In stock", "Historical Fiction"),
    ("Love, Lies and Spies", "£20.55", "In stock", "Historical Fiction"),
    ("A Paris Apartment", "£39.01", "In stock", "Historical Fiction"),
    ("Lilac Girls", "£17.28", "In stock", "Historical Fiction"),
    ("The Constant Princess (The Tudor Court #1)", "£16.62", "In stock", "Historical Fiction"),
    ("The Invention of Wings", "£37.34", "In stock", "Historical Fiction"),
    ("World Without End (The Pillars of the Earth #2)", "£32.97", "In stock", "Historical Fiction"),
    ("The Passion of Dolssa", "£28.32", "In stock", "Historical Fiction"),
    ("Girl With a Pearl Earring", "£26.77", "In stock", "Historical Fiction"),
    ("Voyager (Outlander #3)", "£21.07", "In stock", "Historical Fiction"),
    ("The Red Tent", "£35.66", "In stock", "Historical Fiction"),
    ("The Last Painting of Sara de Vos", "£55.55", "In stock", "Historical Fiction"),
    ("The Guernsey Literary and Potato Peel Pie Society", "£49.53", "In stock", "Historical Fiction"),
    ("Girl in the Blue Coat", "£46.83", "In stock", "Historical Fiction"),
]

if __name__ == "__main__":
    with open("raw_books.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["title", "price_gbp_raw", "star_rating", "availability_raw", "category"])
        for title, price, avail, cat in BOOKS:
            rating = RATINGS[int(hashlib.md5(title.encode()).hexdigest(), 16) % 5]
            w.writerow([title, price, rating, avail, cat])
    print(f"Wrote raw_books.csv: {len(BOOKS)} rows, 3 categories.")
