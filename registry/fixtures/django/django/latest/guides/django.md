# Εγχειρίδιο Django¶

**Source:** https://docs.djangoproject.com/el/6.0/

Εγχειρίδιο Django | Εγχειρίδιο Django | Django

    Skip to main content

  Τεκμηρίωση

    JetBrains Survey

    The Django Software Foundation is once again partnering with JetBrains to run the 2026 Django Developers Survey 📊 Help us better understand how Django is being used around the world and guide future technical and community decisions. Read more on the Django blog.

Please help us spread the word by sharing the survey with your communities and on social media 📣 The more diverse the responses, the better the results for everyone.

      Take the survey ✨

          Getting Help

        Γλώσσα: el

            zh-hans

            sv

            pt-br

            pl

            ko

            ja

            it

            id

            fr

            es

            en

        Έκδοση εγγράφου:
          6.0

            dev

            5.2

            5.1

            5.0

            4.2

            4.1

            4.0

            3.2

            3.1

            3.0

            2.2

            2.1

            2.0

            1.11

            1.10

Εγχειρίδιο Django¶

Όλα όσα χρειάζεται να ξέρετε για το Django.

Πρώτα βήματα¶

Είστε καινούργιος στο Django ή στον προγραμματισμό; Αυτό είναι το κατάλληλο μέρος για να αρχίσετε!

From scratch:
Overview |
Installation

Tutorial:
Part 1: Requests and responses |
Part 2: Models and the admin site |
Part 3: Views and templates |
Part 4: Forms and generic views |
Part 5: Testing |
Part 6: Static files |
Part 7: Customizing the admin site |
Part 8: Adding third-party packages

Advanced Tutorials:
How to write reusable apps |
Writing your first contribution to Django

Μέρη για βοήθεια¶

Έχετε κάποιο πρόβλημα; Θα χαρούμε να σας βοηθήσουμε!

Try the FAQ – it’s got answers to many common questions.

Looking for specific information? Try the Ευρετήριο, Ευρετήριο μονάδων or
the detailed table of contents.

Not found anything? See Συχνές Ερωτήσεις: Λαμβάνοντας βοήθεια for information on getting support
and asking questions to the community.

Αναφέρετε τυχόν bugs του Django στον ticket tracker.

Πως είναι δομημένο το documentation¶

Το Django έχει πολύ documentation. Μια επισκόπηση της οργάνωσης του θα σας βοηθήσει να γνωρίζετε πού να ψάξετε για κάτι συγκεκριμένο:

Tutorials take you by the hand through a series of
steps to create a web application. Start here if you’re new to Django or web
application development. Also look at the «Πρώτα βήματα».

Το άρθρο χρησιμοποιώντας το Django συζητά επιγραμματικά για βασικά θέματα και έννοιες και παρέχει χρήσιμες πληροφορίες και τεκμηριώσεις.

Οι οδηγοί αναφορών περιέχουν τεχνικές αναφορές για τα API και άλλες πτυχές του μηχανισμού του Django. Περιγράφουν πώς λειτουργεί και πώς να το χρησιμοποιήσετε αλλά προϋποθέτει ότι έχετε γνώση βασικών θεμάτων σχετικά με το Django.

Οι οδηγοί how-to είναι συνταγές. Σας καθοδηγούν μέσα από βήματα για την επίλυση κοινών προβλημάτων. Είναι πιο προχωρημένα από τα tutorials και προϋποθέτουν ότι έχετε γνώση του τρόπου λειτουργίας του Django.

Το επίπεδο του μοντέλου (model layer)¶

Django provides an abstraction layer (the «models») for structuring and
manipulating the data of your web application. Learn more about it below:

Models:
Introduction to models |
Field types |
Indexes |
Meta options |
Model class

QuerySets:
Making queries |
QuerySet method reference |
Lookup expressions

Model instances:
Instance methods |
Accessing related objects

Migrations:
Introduction to Migrations |
Operations reference |
SchemaEditor |
Writing migrations

Advanced:
Managers |
Raw SQL |
Transactions |
Aggregation |
Search |
Custom fields |
Multiple databases |
Custom lookups |
Query Expressions |
Conditional Expressions |
Database Functions

Other:
Supported databases |
Legacy databases |
Providing initial data |
Optimize database access |
PostgreSQL specific features

Το επίπεδο του view¶

Το Django έχει την έννοια των «views» για να αναπαραστήσει τη λογική η οποία είναι υπεύθυνη για την επεξεργασία του request του χρήστη και της επιστροφής ενός response. Βρείτε όλα όσα θα θέλατε να μάθετε για τα views παρακάτω:

The basics:
URLconfs |
View functions |
Shortcuts |
Decorators |
Asynchronous Support

Reference:
Built-in Views |
Request/response objects |
TemplateResponse objects

File uploads:
Overview |
File objects |
Storage API |
Managing files |
Custom storage

Class-based views:
Overview |
Built-in display views |
Built-in editing views |
Using mixins |
API reference |
Flattened index

Advanced:
Generating CSV |
Generating PDF

Middleware:
Overview |
Built-in middleware classes

Το επίπεδο template¶

Το επίπεδο template παρέχει ένα φιλικό προς τον designer συντακτικό για να γίνει render η πληροφορία που παρουσιάζεται στον χρήστη. Μάθετε πως αυτό το συντακτικό μπορεί να χρησιμοποιηθεί από τους designers και πως μπορεί να επεκταθεί από τους προγραμματιστές:

The basics:
Overview

For designers:
Language overview |
Built-in tags and filters |
Humanization

For programmers:
Template API |
Custom tags and filters |
Custom template backend

Φόρμες¶

Το Django παρέχει ένα πλούσιο framework για να σας διευκολύνει με την δημιουργία των φορμών και τον χειρισμό των δεδομένων των φορμών (form data).

The basics:
Overview |
Form API |
Built-in fields |
Built-in widgets

Advanced:
Forms for models |
Integrating media |
Formsets |
Customizing validation

Η διαδικασία της ανάπτυξης (development proccess)¶

Μάθετε για τα διάφορα components και εργαλεία του Django προκειμένου να σας βοηθήσουν στην ανάπτυξη και στο testing της εφαρμογής σας:

Settings:
Overview |
Full list of settings

Applications:
Overview

Exceptions:
Overview

django-admin and manage.py:
Overview |
Adding custom commands

Testing:
Introduction |
Writing and running tests |
Included testing tools |
Advanced topics

Deployment:
Overview |
WSGI servers |
ASGI servers |
Deploying static files |
Tracking code errors by email |
Deployment checklist

Το site διαχείρισης¶

Βρείτε όλα όσα θα θέλατε να μάθετε σχετικά με το αυτοματοποιημένο διαχειριστικό site του Django, ένα από τα πιο δημοφιλή features του Django:

Admin site

Admin actions

Admin documentation generator

Ασφάλεια¶

Security is a topic of paramount importance in the development of web
applications and Django provides multiple protection tools and mechanisms:

Security overview

Disclosed security issues in Django

Clickjacking protection

Cross Site Request Forgery protection

Cryptographic signing

Security Middleware

Content Security Policy

Internationalization και localization¶

Το Django προσφέρει ένα ισχυρό και σταθερό framework όσον αφορά το internationalization και το localization προκειμένου να σας βοηθήσει στην ανάπτυξη εφαρμογών σε πολλές γλώσσες και περιοχές ανά τον κόσμο:

Overview |
Internationalization |
Localization |
Localized web UI formatting and form input

Ζώνες ώρας (time zones)

Απόδοση και βελτιστοποίηση¶

Υπάρχουν πολλές τεχνικές και εργαλεία που μπορούν να σας βοηθήσουν στο να κάνετε τον κώδικα σας πιο αποτελεσματικό και γρήγορο, χρησιμοποιώντας λιγότερους πόρους από το σύστημα σας.

Performance and optimization overview

Γεωγραφικό framework¶

GeoDjango intends to be a world-class
geographic web framework. Its goal is to make it as easy as possible to build
GIS web applications and harness the power of spatially enabled data.

Common web application tools¶

Django offers multiple tools commonly needed in the development of web
applications:

Authentication:
Overview |
Using the authentication system |
Password management |
Customizing authentication |
API Reference

Caching

Logging

Tasks framework

Sending emails

Syndication feeds (RSS/Atom)

Pagination

Messages framework

Serialization

Sessions

Sitemaps

Static files management

Data validation

Άλλες κύριες λειτουργίες¶

Μάθετε για άλλες κύριες λειτουργίες του Django framework:

Conditional content processing

Content types and generic relations

Flatpages

Redirects

Signals

System check framework

The sites framework

Unicode in Django

Το ανοιχτού κώδικα project Django¶

Μάθετε για τη διαδικασία ανάπτυξης του Django project και το πώς μπορείτε να συνεισφέρετε:

Community:
Contributing to Django |
The release process |
Team organization |
The Django source code repository |
Security policies |
Mailing lists and Forum

Design philosophies:
Overview

Documentation:
About this documentation

Third-party distributions:
Overview

Django over time:
API stability |
Release notes and upgrading instructions |
Deprecation Timeline

         Back to Top

    Πρόσθετες πληροφορίες

    Support Django!

          twoXAR, Inc, donated to the Django Software Foundation to support Django development. Donate today!

        Μέρη για βοήθεια

          FAQ
          Δοκιμάστε τα FAQ — περιέχουν απαντήσεις σε αρκετές συνηθισμένες ερωτήσεις.

          Ευρετήριο, Ευρετήριο Module, or Πίνακας περιεχομένων
          Χρήησιμο όταν αναζητείτε συγκεκριμένες πληροφορίες.

          Django Discord Server
          Join the Django Discord Community.

          Official Django Forum
          Join the community on the Django Forum.

          Ticket tracker
          Αναφέρετε τυχόν bugs του Django ή του Django documentation στον ticket tracker.

        Κατέβασμα:

          Εκτός σύνδεσης (Django 6.0):
          HTML |
          PDF |
          ePub

            Από το Read the Docs.

    Diamond and Platinum Members

            JetBrains

              JetBrains delivers intelligent software solutions that make developers more productive by simplifying their challenging tasks, automating the routine, and helping them adopt the best development practices. PyCharm is the Python IDE for Professional Developers by JetBrains providing a complete set of tools for productive Python, Web and scientific development.

            Sentry

              Monitor your Django Code
Resolve performance bottlenecks and errors using monitoring, replays, logs and Seer an AI agent for debugging.

            Kraken Tech

              Kraken is the most-loved operating system for energy. Powered by our Utility-Grade AI™ and deep industry know-how, we help utilities transform their technology and operations so they can lead the energy transition. Delivering better outcomes from generation through distribution to supply, Kraken powers 70+ million accounts worldwide, and is on a mission to make a big, green dent in the universe.
