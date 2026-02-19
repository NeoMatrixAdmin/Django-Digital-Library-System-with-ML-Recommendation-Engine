# scraper/utils.py
import hashlib
from urllib.parse import urlparse
import urllib.robotparser
import logging

logger = logging.getLogger(__name__)

def make_fingerprint(title, authors, isbn_list):
    """
    Create a short hash for dedup comparison.
    """
    parts = [title or ""]
    parts.extend(authors or [])
    parts.extend(isbn_list or [])
    joined = "|".join(parts)
    return hashlib.sha1(joined.encode("utf-8")).hexdigest()

def allowed_by_robots(url, user_agent="*"):
    try:
        u = urlparse(url)
        robots_url = f"{u.scheme}://{u.netloc}/robots.txt"
        rp = urllib.robotparser.RobotFileParser()
        rp.set_url(robots_url)
        rp.read()
        return rp.can_fetch(user_agent, url)
    except Exception as e:
        logger.warning("robots.txt check failed for %s: %s", url, e)
        # be conservative: return False if you want strictness, True to proceed. We choose True to avoid blocking due to robots fetch issues.
        return True
