import re
from urllib.parse import urlparse, urljoin, urldefrag
from bs4 import BeautifulSoup
from collections import Counter, defaultdict



#This holds all of our 'statistics' that we will simply just return to the user as a result of our crawl
stats = {
    "unique_pages": set(),
    "longest_page": {"url": "", "words": 0},
    "subdomains": defaultdict(int),
    "word_frequencies": Counter()
}

# Strictly Valid domains according to the assignment
valid_domains = [
            ".ics.uci.edu", 
            ".cs.uci.edu", 
            ".informatics.uci.edu", 
            ".stat.uci.edu"
        ]

#Acquired these stop words from the URL on the assignment page
STOP_WORDS = set([
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are", "aren't", "as", "at", 
    "be", "because", "been", "before", "being", "below", "between", "both", "but", "by", "can't", "cannot", "could", 
    "couldn't", "did", "didn't", "do", "does", "doesn't", "doing", "don't", "down", "during", "each", "few", "for", 
    "from", "further", "had", "hadn't", "has", "hasn't", "have", "haven't", "having", "he", "he'd", "he'll", "he's", 
    "her", "here", "here's", "hers", "herself", "him", "himself", "his", "how", "how's", "i", "i'd", "i'll", "i'm", 
    "i've", "if", "in", "into", "is", "isn't", "it", "it's", "its", "itself", "let's", "me", "more", "most", "mustn't", 
    "my", "myself", "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other", "ought", "our", "ours", 
    "ourselves", "out", "over", "own", "same", "shan't", "she", "she'd", "she'll", "she's", "should", "shouldn't", 
    "so", "some", "such", "than", "that", "that's", "the", "their", "theirs", "them", "themselves", "then", "there", 
    "there's", "these", "they", "they'd", "they'll", "they're", "they've", "this", "those", "through", "to", "too", 
    "under", "until", "up", "very", "was", "wasn't", "we", "we'd", "we'll", "we're", "we've", "were", "weren't", 
    "what", "what's", "when", "when's", "where", "where's", "which", "while", "who", "who's", "whom", "why", "why's", 
    "with", "won't", "would", "wouldn't", "you", "you'd", "you'll", "you're", "you've", "your", "yours", "yourself", 
    "yourselves"
])

def scraper(url, resp):
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]

def extract_next_links(url, resp):
    # Implementation required.
    # url: the URL that was used to get the page
    # resp.url: the actual url of the page
    # resp.status: the status code returned by the server. 200 is OK, you got the page. Other numbers mean that there was some kind of problem.
    # resp.error: when status is not 200, you can check the error here, if needed.
    # resp.raw_response: this is where the page actually is. More specifically, the raw_response has two parts:
    #         resp.raw_response.url: the url, again
    #         resp.raw_response.content: the content of the page!
    # Return a list with the hyperlinks (as strings) scrapped from resp.raw_response.content

    if resp.status !=200:
        return list()
    
    try:
        if not resp.raw_response or not resp.raw_response.content:
            return list()
        
        soup = BeautifulSoup(resp.raw_response.content, 'html.parser')
        clean_url, _ = urldefrag(url)
        stats["unique_pages"].add(clean_url)

        text = soup.get_text(separator=' ', strip = True)
        words = re.split(r'[^a-zA-Z0-9]+', text.lower())
        valid_words = [w for w in words if w and w not in STOP_WORDS and len(w) > 1 and w.isalpha()]

        word_count = len(valid_words)
        if word_count > stats["longest_page"]["words"]:
            stats["longest_page"] = {"url": url, "words": word_count}

        stats["word_frequencies"].update(valid_words)

        parsed_current = urlparse(url)
        if "uci.edu" in parsed_current.netloc:
            subdomain = parsed_current.netloc.lower()
            stats["subdomains"][subdomain] += 1
        

        if len(stats["unique_pages"]) % 50 == 0:
            print(f"[STATS] Unique: {len(stats['unique_pages'])}, Longest: {stats['longest_page']['words']} words")
            save_report()
        
        extracted_links = set()
        for link in soup.find_all('a', href=True):
            raw_link = link['href']
            
            absolute_link = urljoin(url, raw_link)
            
            defrag_link, _ = urldefrag(absolute_link)
            
            extracted_links.add(defrag_link)
            
        return list(extracted_links)


    except Exception as e:
        print(f"Error parsing {url}: {e}")
        return list()

def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    try:
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
            return False
        
        netloc = parsed.netloc.lower()
        if not any(netloc.endswith(domain) or netloc == domain[1:] for domain in valid_domains):
            return False
        

        if re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz|odc|apk|war|pps|xml|json|ppsx|svg|java|sql|sh|zip|tar|7z|rar)$", parsed.path.lower()):
            return False
    
        path_segments = parsed.path.lower().split('/')
        segments = [s for s in path_segments if s]
        if len(segments) >= 3:
            for i in range(len(segments) - 2):
                if segments[i] == segments[i+1] == segments[i+2]:
                    return False

        if "calendar" in parsed.path.lower() or "events" in parsed.path.lower():
            if parsed.query: 
                return False
        if re.search(r'/\d{4}-\d{2}-\d{2}', url):
            return False
        if len(url) > 200:
            return False

        if "C=" in parsed.query and "O=" in parsed.query:
            return False

        if any(x in url for x in [
            "?action=", 
            "?do=", 
            "mediamanager.php", 
            "?idx=", 
            "wp-login.php", 
            "?replytocom=", 
            "?redirect_to=", 
            "?version=", 
            "?timeline", 
            "?format=",
            "/commit/", "/tree/", "/blob/", "/merge_requests/", 
            "?view=", "/branches", "/tags", "/commits/","zip-attachment",       
            "timeline",                  
            "attachment",
        ]):
            return False
        return True

    except TypeError:
        print ("TypeError for ", parsed)
        raise

#doing this to quickly save a report incase crawler crashes
def save_report():
    with open("Crawler_Report.txt", "w") as f:
        f.write("--- CRAWLER REPORT ---\n\n")
        f.write(f"Unique Pages Found: {len(stats['unique_pages'])}\n\n")
        
        f.write("--- LONGEST PAGE ---\n")
        f.write(f"URL: {stats['longest_page']['url']}\n")
        f.write(f"Word Count: {stats['longest_page']['words']}\n\n")
        
        f.write("--- TOP 50 COMMON WORDS ---\n")
        for word, count in stats['word_frequencies'].most_common(50):
            f.write(f"{word}: {count}\n")
        f.write("\n")
        
        f.write("--- SUBDOMAINS ---\n")
        for sub, count in sorted(stats['subdomains'].items()):
            f.write(f"{sub}, {count}\n")    