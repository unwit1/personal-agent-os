"""Precision/recall evaluation of the spam classifier on a synthetic labeled set.

Positive class is 'filtered' (verdict bulk or spam). 'review' verdicts are counted as not
filtered and listed in the operator-review queue. Pure functions, no I/O.
"""
from __future__ import annotations

from .spam import classify

OWN = {"me@example.com", "me@work.example.org"}
KNOWN = {"alice@partner.example.com", "bob@client.example.net", "mom@family.example.com",
         "newsletter@oldfriend.example.com"}


def _m(label, sender, subject, **extra):
    row = {"sender": sender, "subject": subject, "mailbox": "INBOX", "label": label}
    row.update(extra)
    return row


SYNTHETIC: list[dict] = [
    # human: known correspondents and plain first contacts
    _m("human", "Alice <alice@partner.example.com>", "Re: contract draft"),
    _m("human", "bob@client.example.net", "Can you send the invoice numbers?"),
    _m("human", "mom@family.example.com", "Dinner on Sunday?"),
    _m("human", "Carol Diaz <carol@acme.example.com>", "Question about your proposal"),
    _m("human", "dave@startup.example.io", "Intro: meeting next week"),
    _m("human", "erin@university.example.edu", "Following up on our call"),
    _m("human", "frank@lawfirm.example.com", "Please review the attached NDA"),
    _m("human", "grace@candidate.example.com", "Application for senior engineer role"),
    _m("human", "hank@vendor.example.com", "Re: quote request"),
    _m("human", "alice@partner.example.com", "Weekly sync notes", snippet="see you thursday"),
    _m("human", "ivy@clinic.example.com", "Your appointment on Friday"),
    _m("human", "jack@neighbor.example.com", "Sale of the old car - are you interested?"),
    # human, borderline-but-known senders
    _m("human", "newsletter@oldfriend.example.com", "Hey, long time no see"),
    _m("human", "bob@client.example.net", "Quick deal question", list_unsubscribe="<mailto:u@x>"),
    # filtered: server spam folder
    _m("filtered", "x@random.example.biz", "Hello dear friend", mailbox="Junk E-mail"),
    _m("filtered", "y@random.example.biz", "Re: your account", mailbox="INBOX/Spam"),
    # filtered: own sent mail
    _m("filtered", "me@example.com", "Re: contract draft", mailbox="Sent"),
    _m("filtered", "Me <me@work.example.org>", "Notes to self"),
    # filtered: list headers
    _m("filtered", "news@shop.example.com", "Our autumn picks",
       list_unsubscribe="<https://u.example.com/x>", list_id="<picks.shop.example.com>"),
    _m("filtered", "dev-list@lists.example.org", "[dev] patch review",
       list_id="<dev.lists.example.org>", precedence="list"),
    _m("filtered", "editor@magazine.example.com", "This week in tech",
       list_unsubscribe="<mailto:u@m>", precedence="bulk"),
    _m("filtered", "club@gym.example.com", "Your monthly update", precedence="bulk",
       list_unsubscribe="<https://gym.example.com/u>"),
    # filtered: automated senders
    _m("filtered", "noreply@bank.example.com", "Your statement is ready"),
    _m("filtered", "no-reply@github.example.com", "[repo] new comment on issue 12",
       auto_submitted="auto-generated"),
    _m("filtered", "notifications@social.example.com", "You have 3 new followers"),
    _m("filtered", "do-not-reply@airline.example.com", "Check-in opens soon"),
    _m("filtered", "alerts@monitor.example.com", "CPU high on host-7",
       auto_submitted="auto-generated"),
    _m("filtered", "mailer-daemon@mx.example.com", "Delivery Status Notification (Failure)"),
    # filtered: bulk sending domains
    _m("filtered", "store@em.retailer.example.com", "New arrivals just for you",
       list_unsubscribe="<mailto:u@r>"),
    _m("filtered", "deals@mail.sendgrid.net", "50% off everything - shop now"),
    _m("filtered", "promo@mcsv.net", "Limited time: free shipping"),
    # filtered: promotional subjects from first contacts
    _m("filtered", "offers@bigstore.example.com", "Black Friday sale: 40% off, last chance"),
    _m("filtered", "winner@lottery.example.biz", "Giveaway winner - act now!"),
    _m("filtered", "sales@gadgets.example.com", "Exclusive offer: save 30% - don't miss out"),
    _m("filtered", "info@webinars.example.com", "Free webinar + discount coupon inside",
       snippet="click to unsubscribe"),
    _m("filtered", "team@saas.example.com", "Your weekly digest",
       list_unsubscribe="<https://s.example.com/u>"),
    _m("filtered", "hello@brand.example.com", "Spring clearance sale",
       list_unsubscribe="<mailto:u@b>"),
    _m("filtered", "newsletter@substack.example.com", "Issue 42: the newsletter",
       list_id="<n.substack.example.com>"),
    _m("filtered", "marketing@cloud.example.com", "Cyber Monday deals for you"),
    _m("filtered", "billing@utility.example.com", "Invoice available",
       list_unsubscribe="<mailto:u@u>", precedence="bulk"),
    # deliberately borderline: weak signals only -> review queue
    _m("human", "info@community.example.org", "Webinar invite: neighborhood meeting"),
    _m("filtered", "support@tool.example.com", "Product update: new dashboard",
       snippet="unsubscribe here"),
    _m("human", "orders@localbakery.example.com", "Your cake order - discount applied"),
    _m("human", "team@friends.example.com", "Weekend deal: dinner at 8?"),
]


def evaluate(labeled=None, own=None, known=None) -> dict:
    labeled = SYNTHETIC if labeled is None else labeled
    own = OWN if own is None else own
    known = KNOWN if known is None else known
    tp = fp = fn = tn = 0
    review_queue = []
    for item in labeled:
        verdict = classify(item, own=set(own), known=set(known))
        predicted = verdict["verdict"] in ("bulk", "spam")
        actual = item["label"] == "filtered"
        if verdict["verdict"] == "review":
            review_queue.append({"subject": item.get("subject", ""),
                                 "sender": item.get("sender", ""),
                                 "reasons": list(verdict["reasons"])})
        if predicted and actual:
            tp += 1
        elif predicted:
            fp += 1
        elif actual:
            fn += 1
        else:
            tn += 1
    return {
        "precision": tp / (tp + fp) if tp + fp else 1.0,
        "recall": tp / (tp + fn) if tp + fn else 1.0,
        "tp": tp, "fp": fp, "fn": fn, "tn": tn,
        "review_queue": review_queue,
    }
