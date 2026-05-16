# LLM test file&para;

**Source:** https://fastapi.tiangolo.com/_llm-test/

LLM test file - FastAPI

          Skip to content

         Join the FastAPI Cloud waiting list 🚀

         FastAPI Conf '26 — Oct 28, 2026, Amsterdam 🎤

         Follow @fastapi on X (Twitter) to stay updated

         Follow FastAPI on LinkedIn to stay updated

         Subscribe to the FastAPI and friends newsletter 🎉

        sponsor

        sponsor

        sponsor

        sponsor

        sponsor

        sponsor

        sponsor

        sponsor

        sponsor

        sponsor

    Security

      Middleware

      CORS (Cross-Origin Resource Sharing)

      SQL (Relational) Databases

      Bigger Applications - Multiple Files

      Stream JSON Lines

      Server-Sent Events (SSE)

      Background Tasks

      Metadata and Docs URLs

      Static Files

      Testing

      Debugging

    Advanced User Guide

      Using the Request Directly

      Using Dataclasses

      Advanced Middleware

      Sub Applications - Mounts

      Behind a Proxy

      Templates

      WebSockets

      Lifespan Events

      Testing WebSockets

      Testing Events: lifespan and startup - shutdown

      Testing Dependencies with Overrides

      Async Tests

      Settings and Environment Variables

      OpenAPI Callbacks

      OpenAPI Webhooks

      Including WSGI - Flask, Django, others

      Generating SDKs

      Advanced Python Types

      JSON with Bytes as Base64

      Strict Content-Type Checking

      FastAPI CLI

      Editor Support

    Deployment

    How To - Recipes

    Reference

      Security Tools

      Encoders - jsonable_encoder

      Static Files - StaticFiles

      Templating - Jinja2Templates

      Test Client - TestClient

      FastAPI People

    Resources

    About

      Release Notes

          HTML "dfn" elements

          Headings

          Terms used in the docs

LLM test file&para;

This document tests if the LLM, which translates the documentation, understands the general_prompt in scripts/translate.py and the language specific prompt in docs/{language code}/llm-prompt.md. The language specific prompt is appended to general_prompt.

Tests added here will be seen by all designers of language specific prompts.

Use as follows:

Have a language specific prompt - docs/{language code}/llm-prompt.md.

Do a fresh translation of this document into your desired target language (see e.g. the translate-page command of the translate.py). This will create the translation under docs/{language code}/docs/_llm-test.md.

Check if things are okay in the translation.

If necessary, improve your language specific prompt, the general prompt, or the English document.

Then manually fix the remaining issues in the translation, so that it is a good translation.

Retranslate, having the good translation in place. The ideal result would be that the LLM makes no changes anymore to the translation. That means that the general prompt and your language specific prompt are as good as they can be (It will sometimes make a few seemingly random changes, the reason is that LLMs are not deterministic algorithms).

The tests:

Code snippets&para;

TestInfo

This is a code snippet: foo. And this is another code snippet: bar. And another one: baz quux.

Content of code snippets should be left as is.

See section ### Content of code snippets in the general prompt in scripts/translate.py.

Quotes&para;

TestInfo

Yesterday, my friend wrote: "If you spell incorrectly correctly, you have spelled it incorrectly". To which I answered: "Correct, but 'incorrectly' is incorrectly not '"incorrectly"'".

Note

The LLM will probably translate this wrong. Interesting is only if it keeps the fixed translation when retranslating.

The prompt designer may choose if they want to convert neutral quotes to typographic quotes. It is okay to leave them as is.

See for example section ### Quotes in docs/de/llm-prompt.md.

Quotes in code snippets&para;

TestInfo

pip install "foo[bar]"

Examples for string literals in code snippets: "this", 'that'.

A difficult example for string literals in code snippets: f"I like {'oranges' if orange else "apples"}"

Hardcore: Yesterday, my friend wrote: "If you spell incorrectly correctly, you have spelled it incorrectly". To which I answered: "Correct, but 'incorrectly' is incorrectly not '"incorrectly"'"

... However, quotes inside code snippets must stay as is.

code blocks&para;

TestInfo

A Bash code example...

# Print a greeting to the universe
echo &quot;Hello universe&quot;

...and a console code example...

$ <font color=&quot;#4E9A06&quot;>fastapi</font> run <u style=&quot;text-decoration-style:solid&quot;>main.py</u>
<span style=&quot;background-color:#009485&quot;><font color=&quot;#D3D7CF&quot;> FastAPI </font></span>  Starting server
        Searching for package file structure

...and another console code example...

// Create a directory &quot;Code&quot;
$ mkdir code
// Switch into that directory
$ cd code

...and a Python code example...

wont_work()  # This won&#39;t work 😱
works(foo=&quot;bar&quot;)  # This works 🎉

...and that's it.

Code in code blocks should not be modified, with the exception of comments.

See section ### Content of code blocks in the general prompt in scripts/translate.py.

Tabs and colored boxes&para;

TestInfo

Info

Some text

Note

Some text

Technical details

Some text

Check

Some text

Tip

Some text

Warning

Some text

Danger

Some text

Tabs and Info/Note/Warning/etc. blocks should have the translation of their title added after a vertical bar (|).

See sections ### Special blocks and ### Tab blocks in the general prompt in scripts/translate.py.

Web- and internal links&para;

TestInfo

The link text should get translated, the link address should remain unchanged:

Link to heading above

Internal link

External link

Link to a style

Link to a script

Link to an image

The link text should get translated, the link address should point to the translation:

FastAPI link

Links should be translated, but their address shall remain unchanged. An exception are absolute links to pages of the FastAPI documentation. In that case it should link to the translation.

See section ### Links in the general prompt in scripts/translate.py.

HTML "abbr" elements&para;

TestInfo

Here some things wrapped in HTML "abbr" elements (Some are invented):

The abbr gives a full phrase&para;

GTD

lt

XWT

PSGI

The abbr gives a full phrase and an explanation&para;

MDN

I/O.

"title" attributes of "abbr" elements are translated following some specific instructions.

Translations can add their own "abbr" elements which the LLM should not remove. E.g. to explain English words.

See section ### HTML abbr elements in the general prompt in scripts/translate.py.

HTML "dfn" elements&para;

cluster

Deep Learning

Headings&para;

TestInfo

Develop a webapp - a tutorial&para;

Hello.

Type hints and -annotations&para;

Hello again.

Super- and subclasses&para;

Hello again.

The only hard rule for headings is that the LLM leaves the hash part inside curly brackets unchanged, which ensures that links do not break.

See section ### Headings in the general prompt in scripts/translate.py.

For some language specific instructions, see e.g. section ### Headings in docs/de/llm-prompt.md.

Terms used in the docs&para;

TestInfo

you

your

e.g.

etc.

foo as an int

bar as a str

baz as a list

the Tutorial - User guide

the Advanced User Guide

the SQLModel docs

the API docs

the automatic docs

Data Science

Deep Learning

Machine Learning

Dependency Injection

HTTP Basic authentication

HTTP Digest

ISO format

the JSON Schema standard

the JSON schema

the schema definition

Password Flow

Mobile

deprecated

designed

invalid

on the fly

standard

default

case-sensitive

case-insensitive

to serve the application

to serve the page

the app

the application

the request

the response

the error response

the path operation

the path operation decorator

the path operation function

the body

the request body

the response body

the JSON body

the form body

the file body

the function body

the parameter

the body parameter

the path parameter

the query parameter

the cookie parameter

the header parameter

the form parameter

the function parameter

the event

the startup event

the startup of the server

the shutdown event

the lifespan event

the handler

the event handler

the exception handler

to handle

the model

the Pydantic model

the data model

the database model

the form model

the model object

the class

the base class

the parent class

the subclass

the child class

the sibling class

the class method

the header

the headers

the authorization header

the Authorization header

the forwarded header

the dependency injection system

the dependency

the dependable

the dependant

I/O bound

CPU bound

concurrency

parallelism

multiprocessing

the env var

the environment variable

the PATH

the PATH variable

the authentication

the authentication provider

the authorization

the authorization form

the authorization provider

the user authenticates

the system authenticates the user

the CLI

the command line interface

the server

the client

the cloud provider

the cloud service

the development

the development stages

the dict

the dictionary

the enumeration

the enum

the enum member

the encoder

the decoder

to encode

to decode

the exception

to raise

the expression

the statement

the frontend

the backend

the GitHub discussion

the GitHub issue

the performance

the performance optimization

the return type

the return value

the security

the security scheme

the task

the background task

the task function

the template

the template engine

the type annotation

the type hint

the server worker

the Uvicorn worker

the Gunicorn Worker

the worker process

the worker class

the workload

the deployment

to deploy

the SDK

the software development kit

the APIRouter

the requirements.txt

the Bearer Token

the breaking change

the bug

the button

the callable

the code

the commit

the context manager

the coroutine

the database session

the disk

the domain

the engine

the fake X

the HTTP GET method

the item

the library

the lifespan

the lock

the middleware

the mobile application

the module

the mounting

the network

the origin

the override

the payload

the processor

the property

the proxy

the pull request

the query

the RAM

the remote machine

the status code

the string

the tag

the web framework

the wildcard

to return

to validate

This is a not complete and not normative list of (mostly) technical terms seen in the docs. It may be helpful for the prompt designer to figure out for which terms the LLM needs a helping hand. For example when it keeps reverting a good translation to a suboptimal translation. Or when it has problems conjugating/declinating a term in your language.

See e.g. section ### List of English terms and their preferred German translations in docs/de/llm-prompt.md.

  Back to top
