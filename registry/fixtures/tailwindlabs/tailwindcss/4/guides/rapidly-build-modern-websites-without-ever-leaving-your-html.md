# Rapidly build modern websites without ever leaving your HTML.

**Source:** https://tailwindcss.com/

Tailwind CSS - Rapidly build modern websites without ever leaving your HTML.
v4.3
⌘KCtrl KDocsBlogShowcasePartnersPlus

text-4xl text-5xl text-6xl text-8xl text-gray-950 text-white tracking-tighter text-balance
Rapidly build modern websites without ever leaving your HTML.

text-lg text-gray-950text-white font-medium
A utility-first CSS framework packed with classes like flex, pt-4, text-center and rotate-90 that can be composed to build any design, directly in your markup.

Get started
Get startedQuick search⌘KCtrl K

<div class=&quot;flex flex-col items-center rounded-2xl&quot;>  <div>    <img class=&quot;size-48 shadow-xl&quot; alt=&quot;&quot; src=&quot;/img/cover.png&quot; />  </div>  <div class=&quot;flex&quot;>    <span>Class Warfare</span>    <span>The Anti-Patterns</span>    <span class=&quot;flex&quot;>      <span>No. 4</span>      <span>·</span>      <span>2025</span>    </span>  </div></div>

Class WarfareThe Anti-PatternsNo. 4·2025

text-4xl text-gray-950text-white tracking-tighter text-balance
Sponsors

Supported by the best.

text-base text-gray-950text-white
Tailwind is supported by incredible partners and sponsors who make it possible for a team of talented designers and engineers to maintain the framework full-time.

Become a sponsor

text-4xl text-gray-950text-white tracking-tighter text-balance
Why Tailwind CSS?

Built for the modern web.

text-base text-gray-950text-white
Tailwind is unapologetically modern, and takes advantage of all the latest and greatest CSS features to make the developer experience as enjoyable as possible.

Responsive designOkay, it’s not exactly cutting edge, but just throw a screen size in front of literally any utility to apply it at a specific breakpoint.

Mobile

sm

md

lg

xl

Entire houseBeach House on Lake Huron

Entire houseBeach House on Lake Huron2.66(128 reviews)·Bayfield, ON
Check availability

This sunny and spacious room is for those traveling light and looking for a comfy and cozy place to lay their head for a night... Show more
Show more
Check availability

FiltersWhat’s a website these days without a few backdrop blurs? Keep stacking filters until your designer asks you to please, please stop.

blur-sm

brightness-150

grayscale

contrast-150

saturate-200

sepia

Dark modeIf you’re not a fan of burning your retinas, just stick dark: in front of any color to apply it in dark mode.

CSS variablesCustomizing your theme is as simple as creating a few CSS variables.

@theme {  --font-sans: "Inter", sans-serif;  --font-mono: "IBM Plex Mono", monospace;  --text-tiny: 0.625rem;  --text-tiny--line-height: 1.5rem;  --color-mint-100: oklch(0.97 0.15 145);  --color-mint-200: oklch(0.92 0.18 145);  --color-mint-300: oklch(0.85 0.22 145);  --color-mint-400: oklch(0.78 0.25 145);  --color-mint-500: oklch(0.7 0.28 145);  --color-mint-600: oklch(0.63 0.3 145);  --color-mint-700: oklch(0.56 0.32 145);  --color-mint-800: oklch(0.48 0.35 145);  --color-mint-900: oklch(0.4 0.37 145);  --color-mint-950: oklch(0.3 0.4 145);}

P3 colorsThe color palette now uses more vibrant wide gamut colors without you needing to understand what any of that even means.

red

orange

amber

yellow

lime

green

emerald

teal

cyan

sky

blue

indigo

violet

purple

fuchsia

pink

rose

950

900

800

700

600

500

400

300

200

100

50

CSS grid layoutUsing grid utilities directly in your HTML makes it so much easier to reason about complex layouts.

Browse properties
Treehouses

Mansions

Lakefront cottages

Designer homes

Transitions and animationsTransitions that work the way you&#x27;d expect — throw a few utilities on an element and you&#x27;re in business.

transition duration-750linear

transition duration-750ease-out

transition duration-750ease-in-out

transition duration-750ease-in

Cascade layersTailwind uses CSS layers so you don’t have to worry about specificity issues.

@layer theme, base, components, utilities;@layer theme {  :root {    /* Your theme variables */  }}@layer base {  /* Preflight styles */}@layer components {  /* Your custom components */}@layer utilities {  /* Your utility classes */}

Logical propertiesSupporting multiple language text directions is no longer a nightmare.

ltr

rtl

Will WintonDirector of Operations

Kristin YardlyMarketing Coordinator

Emanual CuccittiniStaff Engineer

Kiara SmithVP of Engineering

سارة أحمدمديرة مشاريع

علي محمدمطور برمجيات

خالد عمرمصمم واجهات المستخدم

Container queriesTag an element as a container to let children adapt to changes in its size.

&#x3C;div class="@container">  &#x3C;div class="grid grid-cols-1 @sm:grid-cols-2">    &#x3C;img      src="/img/photo-1.jpg"      class="aspect-square @sm:aspect-3/2 object-cover"    />    &#x3C;img      src="/img/photo-2.jpg"      class="aspect-square @sm:aspect-3/2 object-cover"    />    &#x3C;img      src="/img/photo-3.jpg"      class="aspect-square @sm:aspect-3/2 object-cover"    />    &#x3C;img      src="/img/photo-4.jpg"      class="aspect-square @sm:aspect-3/2 object-cover"    />  &#x3C;/div>&#x3C;/div>

GradientsNo need to remember that complicated gradient syntax — create silky-smooth gradients with just a few utility classes.

Power Meets PrecisionRedefining real-time performance
Our next-generation rendering engine delivers unmatched speed and efficiency, empowering creators to push boundaries like never before.

Render time performance

6.4x
Real-time frame rate

4.2x
Multi-platform build time

2.7x

3D transformsSometimes two dimensions aren’t enough. Scale, rotate, and translate any element in 3D space to add a touch of depth.

text-4xl text-gray-950text-white tracking-tighter text-balance
How it works

Ship faster and smaller.

text-base text-gray-950text-white
Tailwind automatically removes all unused CSS when building for production, which means your final CSS bundle is the smallest it could possibly be. In fact, most Tailwind projects ship less than 10kB of CSS to the client.

index.htmlapp.csspackage.json
<!DOCTYPE html><html lang=&quot;en&quot;>  <head>    <meta charset=&quot;UTF-8&quot; />    <meta name=&quot;viewport&quot; content=&quot;width=device-width, initial-scale=1.0&quot; />    <title>Tailwind CSS</title>    <link rel=&quot;stylesheet&quot; href=&quot;/build.css&quot; />  </head>  <body>    <button class=&quot;&quot;></button>  </body></html>

Terminal

build.css
@layer utilities {}

text-4xl text-gray-950text-white tracking-tighter
Tailwind in the wild

Build whatever you want, without touching your CSS file.

text-base text-gray-950text-white
Because Tailwind is so low-level, it never encourages you to design the same site twice. Some of your favorite sites are built with Tailwind, and you probably had no idea.

openai.com
opalcamera.com
feastables.com

gumroad.com
skims.com
reddit.com

rivian.com
shopify.com
clerk.dev

theverge.com
io.google
ted.com

poolside.ai
midjourney.com
jpl.nasa.gov

text-4xl text-gray-950text-white tracking-tighter text-balance
Ready-made Components

Move even faster with Tailwind Plus.

text-base text-gray-950text-white
Tailwind Plus is a collection of beautiful, fully responsive UI components, designed and developed by us, the creators of Tailwind CSS. It&#x27;s got hundreds of ready-to-use examples to choose from, and is guaranteed to help you find the perfect starting point for what you want to build.

Explore Tailwind Plus

Templates
Visually-stunning, easy to customize site templates built with React and Next.js.

UI Blocks
Over 500+ professionally designed, fully responsive, expertly crafted components.

UI Kit
A starter kit for building your own component systems with React and Tailwind CSS.

Copyright © 2026 Tailwind Labs Inc.·Trademark Policy
