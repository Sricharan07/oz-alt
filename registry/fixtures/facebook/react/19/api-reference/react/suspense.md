# &lt;Suspense&gt;

**Source:** https://react.dev/reference/react/Suspense

<Suspense> – React

API Reference
Components

Copy pageCopy
<Suspense>

<Suspense> lets you display a fallback until its children have finished loading.
<Suspense fallback={<Loading />}>

  <SomeComponent />

</Suspense>

Reference <Suspense>

Usage Displaying a fallback while content is loading
Revealing content together at once
Revealing nested content as it loads
Showing stale content while fresh content is loading
Preventing already revealed content from hiding
Indicating that a Transition is happening
Resetting Suspense boundaries on navigation
Providing a fallback for server errors and client-only content

Troubleshooting How do I prevent the UI from being replaced by a fallback during an update?

Reference

<Suspense>

Props

children: The actual UI you intend to render. If children suspends while rendering, the Suspense boundary will switch to rendering fallback.

fallback: An alternate UI to render in place of the actual UI if it has not finished loading. Any valid React node is accepted, though in practice, a fallback is a lightweight placeholder view, such as a loading spinner or skeleton. Suspense will automatically switch to fallback when children suspends, and back to children when the data is ready. If fallback suspends while rendering, it will activate the closest parent Suspense boundary.

Caveats

React does not preserve any state for renders that got suspended before they were able to mount for the first time. When the component has loaded, React will retry rendering the suspended tree from scratch.

If Suspense was displaying content for the tree, but then it suspended again, the fallback will be shown again unless the update causing it was caused by startTransition or useDeferredValue.

If React needs to hide the already visible content because it suspended again, it will clean up layout Effects in the content tree. When the content is ready to be shown again, React will fire the layout Effects again. This ensures that Effects measuring the DOM layout don’t try to do this while the content is hidden.

React includes under-the-hood optimizations like Streaming Server Rendering and Selective Hydration that are integrated with Suspense. Read an architectural overview and watch a technical talk to learn more.

Usage

Displaying a fallback while content is loading

You can wrap any part of your application with a Suspense boundary:

<Suspense fallback={<Loading />}>

  <Albums />

</Suspense>

React will display your loading fallback until all the code and data needed by the children has been loaded.

In the example below, the Albums component suspends while fetching the list of albums. Until it’s ready to render, React switches the closest Suspense boundary above to show the fallback—your Loading component. Then, when the data loads, React hides the Loading fallback and renders the Albums component with data.

ArtistPage.jsAlbums.js

ArtistPage.js

ReloadClearFork

import { Suspense } from &#x27;react&#x27;;
import Albums from &#x27;./Albums.js&#x27;;

export default function ArtistPage({ artist }) {
  return (
    <>
      <h1>{artist.name}</h1>
      <Suspense fallback={<Loading />}>
        <Albums artistId={artist.id} />
      </Suspense>
    </>
  );
}

function Loading() {
  return <h2>🌀 Loading...</h2>;
}

Show more

Note
Only Suspense-enabled data sources will activate the Suspense component. They include:

Data fetching with Suspense-enabled frameworks like Relay and Next.js

Lazy-loading component code with lazy

Reading the value of a cached Promise with use

Suspense does not detect when data is fetched inside an Effect or event handler.
The exact way you would load data in the Albums component above depends on your framework. If you use a Suspense-enabled framework, you’ll find the details in its data fetching documentation.
Suspense-enabled data fetching without the use of an opinionated framework is not yet supported. The requirements for implementing a Suspense-enabled data source are unstable and undocumented. An official API for integrating data sources with Suspense will be released in a future version of React.

Revealing content together at once

By default, the whole tree inside Suspense is treated as a single unit. For example, even if only one of these components suspends waiting for some data, all of them together will be replaced by the loading indicator:

<Suspense fallback={<Loading />}>

  <Biography />

  <Panel>

    <Albums />

  </Panel>

</Suspense>

Then, after all of them are ready to be displayed, they will all appear together at once.

In the example below, both Biography and Albums fetch some data. However, because they are grouped under a single Suspense boundary, these components always “pop in” together at the same time.

ArtistPage.jsPanel.jsBiography.jsAlbums.js

ArtistPage.js

ReloadClearFork

import { Suspense } from &#x27;react&#x27;;
import Albums from &#x27;./Albums.js&#x27;;
import Biography from &#x27;./Biography.js&#x27;;
import Panel from &#x27;./Panel.js&#x27;;

export default function ArtistPage({ artist }) {
  return (
    <>
      <h1>{artist.name}</h1>
      <Suspense fallback={<Loading />}>
        <Biography artistId={artist.id} />
        <Panel>
          <Albums artistId={artist.id} />
        </Panel>
      </Suspense>
    </>
  );
}

function Loading() {
  return <h2>🌀 Loading...</h2>;
}

Show more

Components that load data don’t have to be direct children of the Suspense boundary. For example, you can move Biography and Albums into a new Details component. This doesn’t change the behavior. Biography and Albums share the same closest parent Suspense boundary, so their reveal is coordinated together.

<Suspense fallback={<Loading />}>

  <Details artistId={artist.id} />

</Suspense>

function Details({ artistId }) {

  return (

    <>

      <Biography artistId={artistId} />

      <Panel>

        <Albums artistId={artistId} />

      </Panel>

    </>

  );

}

Revealing nested content as it loads

When a component suspends, the closest parent Suspense component shows the fallback. This lets you nest multiple Suspense components to create a loading sequence. Each Suspense boundary’s fallback will be filled in as the next level of content becomes available. For example, you can give the album list its own fallback:

<Suspense fallback={<BigSpinner />}>

  <Biography />

  <Suspense fallback={<AlbumsGlimmer />}>

    <Panel>

      <Albums />

    </Panel>

  </Suspense>

</Suspense>

With this change, displaying the Biography doesn’t need to “wait” for the Albums to load.

The sequence will be:

If Biography hasn’t loaded yet, BigSpinner is shown in place of the entire content area.

Once Biography finishes loading, BigSpinner is replaced by the content.

If Albums hasn’t loaded yet, AlbumsGlimmer is shown in place of Albums and its parent Panel.

Finally, once Albums finishes loading, it replaces AlbumsGlimmer.

ArtistPage.jsPanel.jsBiography.jsAlbums.js

ArtistPage.js

ReloadClearFork

import { Suspense } from &#x27;react&#x27;;
import Albums from &#x27;./Albums.js&#x27;;
import Biography from &#x27;./Biography.js&#x27;;
import Panel from &#x27;./Panel.js&#x27;;

export default function ArtistPage({ artist }) {
  return (
    <>
      <h1>{artist.name}</h1>
      <Suspense fallback={<BigSpinner />}>
        <Biography artistId={artist.id} />
        <Suspense fallback={<AlbumsGlimmer />}>
          <Panel>
            <Albums artistId={artist.id} />
          </Panel>
        </Suspense>
      </Suspense>
    </>
  );
}

function BigSpinner() {
  return <h2>🌀 Loading...</h2>;
}

function AlbumsGlimmer() {
  return (
    <div className=&quot;glimmer-panel&quot;>
      <div className=&quot;glimmer-line&quot; />
      <div className=&quot;glimmer-line&quot; />
      <div className=&quot;glimmer-line&quot; />
    </div>
  );
}

Show more

Suspense boundaries let you coordinate which parts of your UI should always “pop in” together at the same time, and which parts should progressively reveal more content in a sequence of loading states. You can add, move, or delete Suspense boundaries in any place in the tree without affecting the rest of your app’s behavior.

Don’t put a Suspense boundary around every component. Suspense boundaries should not be more granular than the loading sequence that you want the user to experience. If you work with a designer, ask them where the loading states should be placed—it’s likely that they’ve already included them in their design wireframes.

Showing stale content while fresh content is loading

In this example, the SearchResults component suspends while fetching the search results. Type &quot;a&quot;, wait for the results, and then edit it to &quot;ab&quot;. The results for &quot;a&quot; will get replaced by the loading fallback.

App.jsSearchResults.js

App.js

ReloadClearFork

import { Suspense, useState } from &#x27;react&#x27;;
import SearchResults from &#x27;./SearchResults.js&#x27;;

export default function App() {
  const [query, setQuery] = useState(&#x27;&#x27;);
  return (
    <>
      <label>
        Search albums:
        <input value={query} onChange={e => setQuery(e.target.value)} />
      </label>
      <Suspense fallback={<h2>Loading...</h2>}>
        <SearchResults query={query} />
      </Suspense>
    </>
  );
}

Show more

A common alternative UI pattern is to defer updating the list and to keep showing the previous results until the new results are ready. The useDeferredValue Hook lets you pass a deferred version of the query down:

export default function App() {

  const [query, setQuery] = useState(&#x27;&#x27;);

  const deferredQuery = useDeferredValue(query);

  return (

    <>

      <label>

        Search albums:

        <input value={query} onChange={e => setQuery(e.target.value)} />

      </label>

      <Suspense fallback={<h2>Loading...</h2>}>

        <SearchResults query={deferredQuery} />

      </Suspense>

    </>

  );

}

The query will update immediately, so the input will display the new value. However, the deferredQuery will keep its previous value until the data has loaded, so SearchResults will show the stale results for a bit.

To make it more obvious to the user, you can add a visual indication when the stale result list is displayed:

<div style={{

  opacity: query !== deferredQuery ? 0.5 : 1

}}>

  <SearchResults query={deferredQuery} />

</div>

Enter &quot;a&quot; in the example below, wait for the results to load, and then edit the input to &quot;ab&quot;. Notice how instead of the Suspense fallback, you now see the dimmed stale result list until the new results have loaded:

App.js

App.js

ReloadClearFork

import { Suspense, useState, useDeferredValue } from &#x27;react&#x27;;
import SearchResults from &#x27;./SearchResults.js&#x27;;

export default function App() {
  const [query, setQuery] = useState(&#x27;&#x27;);
  const deferredQuery = useDeferredValue(query);
  const isStale = query !== deferredQuery;
  return (
    <>
      <label>
        Search albums:
        <input value={query} onChange={e => setQuery(e.target.value)} />
      </label>
      <Suspense fallback={<h2>Loading...</h2>}>
        <div style={{ opacity: isStale ? 0.5 : 1 }}>
          <SearchResults query={deferredQuery} />
        </div>
      </Suspense>
    </>
  );
}

Show more

Note
Both deferred values and Transitions let you avoid showing Suspense fallback in favor of inline indicators. Transitions mark the whole update as non-urgent so they are typically used by frameworks and router libraries for navigation. Deferred values, on the other hand, are mostly useful in application code where you want to mark a part of UI as non-urgent and let it “lag behind” the rest of the UI.

Preventing already revealed content from hiding

When a component suspends, the closest parent Suspense boundary switches to showing the fallback. This can lead to a jarring user experience if it was already displaying some content. Try pressing this button:

App.jsLayout.jsIndexPage.jsArtistPage.jsAlbums.jsBiography.jsPanel.js

App.js

ReloadClearFork

import { Suspense, useState } from &#x27;react&#x27;;
import IndexPage from &#x27;./IndexPage.js&#x27;;
import ArtistPage from &#x27;./ArtistPage.js&#x27;;
import Layout from &#x27;./Layout.js&#x27;;

export default function App() {
  return (
    <Suspense fallback={<BigSpinner />}>
      <Router />
    </Suspense>
  );
}

function Router() {
  const [page, setPage] = useState(&#x27;/&#x27;);

  function navigate(url) {
    setPage(url);
  }

  let content;
  if (page === &#x27;/&#x27;) {
    content = (
      <IndexPage navigate={navigate} />
    );
  } else if (page === &#x27;/the-beatles&#x27;) {
    content = (
      <ArtistPage
        artist={{
          id: &#x27;the-beatles&#x27;,
          name: &#x27;The Beatles&#x27;,
        }}
      />
    );
  }
  return (
    <Layout>
      {content}
    </Layout>
  );
}

function BigSpinner() {
  return <h2>🌀 Loading...</h2>;
}

Show more

When you pressed the button, the Router component rendered ArtistPage instead of IndexPage. A component inside ArtistPage suspended, so the closest Suspense boundary started showing the fallback. The closest Suspense boundary was near the root, so the whole site layout got replaced by BigSpinner.

To prevent this, you can mark the navigation state update as a Transition with startTransition:

function Router() {

  const [page, setPage] = useState(&#x27;/&#x27;);

  function navigate(url) {

    startTransition(() => {

      setPage(url);

    });

  }

  // ...

This tells React that the state transition is not urgent, and it’s better to keep showing the previous page instead of hiding any already revealed content. Now clicking the button “waits” for the Biography to load:

App.jsLayout.jsIndexPage.jsArtistPage.jsAlbums.jsBiography.jsPanel.js

App.js

ReloadClearFork

import { Suspense, startTransition, useState } from &#x27;react&#x27;;
import IndexPage from &#x27;./IndexPage.js&#x27;;
import ArtistPage from &#x27;./ArtistPage.js&#x27;;
import Layout from &#x27;./Layout.js&#x27;;

export default function App() {
  return (
    <Suspense fallback={<BigSpinner />}>
      <Router />
    </Suspense>
  );
}

function Router() {
  const [page, setPage] = useState(&#x27;/&#x27;);

  function navigate(url) {
    startTransition(() => {
      setPage(url);
    });
  }

  let content;
  if (page === &#x27;/&#x27;) {
    content = (
      <IndexPage navigate={navigate} />
    );
  } else if (page === &#x27;/the-beatles&#x27;) {
    content = (
      <ArtistPage
        artist={{
          id: &#x27;the-beatles&#x27;,
          name: &#x27;The Beatles&#x27;,
        }}
      />
    );
  }
  return (
    <Layout>
      {content}
    </Layout>
  );
}

function BigSpinner() {
  return <h2>🌀 Loading...</h2>;
}

Show more

A Transition doesn’t wait for all content to load. It only waits long enough to avoid hiding already revealed content. For example, the website Layout was already revealed, so it would be bad to hide it behind a loading spinner. However, the nested Suspense boundary around Albums is new, so the Transition doesn’t wait for it.

Note
Suspense-enabled routers are expected to wrap the navigation updates into Transitions by default.

Indicating that a Transition is happening

In the above example, once you click the button, there is no visual indication that a navigation is in progress. To add an indicator, you can replace startTransition with useTransition which gives you a boolean isPending value. In the example below, it’s used to change the website header styling while a Transition is happening:

App.jsLayout.jsIndexPage.jsArtistPage.jsAlbums.jsBiography.jsPanel.js

App.js

ReloadClearFork

import { Suspense, useState, useTransition } from &#x27;react&#x27;;
import IndexPage from &#x27;./IndexPage.js&#x27;;
import ArtistPage from &#x27;./ArtistPage.js&#x27;;
import Layout from &#x27;./Layout.js&#x27;;

export default function App() {
  return (
    <Suspense fallback={<BigSpinner />}>
      <Router />
    </Suspense>
  );
}

function Router() {
  const [page, setPage] = useState(&#x27;/&#x27;);
  const [isPending, startTransition] = useTransition();

  function navigate(url) {
    startTransition(() => {
      setPage(url);
    });
  }

  let content;
  if (page === &#x27;/&#x27;) {
    content = (
      <IndexPage navigate={navigate} />
    );
  } else if (page === &#x27;/the-beatles&#x27;) {
    content = (
      <ArtistPage
        artist={{
          id: &#x27;the-beatles&#x27;,
          name: &#x27;The Beatles&#x27;,
        }}
      />
    );
  }
  return (
    <Layout isPending={isPending}>
      {content}
    </Layout>
  );
}

function BigSpinner() {
  return <h2>🌀 Loading...</h2>;
}

Show more

Resetting Suspense boundaries on navigation

During a Transition, React will avoid hiding already revealed content. However, if you navigate to a route with different parameters, you might want to tell React it is different content. You can express this with a key:

<ProfilePage key={queryParams.id} />

Imagine you’re navigating within a user’s profile page, and something suspends. If that update is wrapped in a Transition, it will not trigger the fallback for already visible content. That’s the expected behavior.

However, now imagine you’re navigating between two different user profiles. In that case, it makes sense to show the fallback. For example, one user’s timeline is different content from another user’s timeline. By specifying a key, you ensure that React treats different users’ profiles as different components, and resets the Suspense boundaries during navigation. Suspense-integrated routers should do this automatically.

Providing a fallback for server errors and client-only content

If you use one of the streaming server rendering APIs (or a framework that relies on them), React will also use your <Suspense> boundaries to handle errors on the server. If a component throws an error on the server, React will not abort the server render. Instead, it will find the closest <Suspense> component above it and include its fallback (such as a spinner) into the generated server HTML. The user will see a spinner at first.

On the client, React will attempt to render the same component again. If it errors on the client too, React will throw the error and display the closest Error Boundary. However, if it does not error on the client, React will not display the error to the user since the content was eventually displayed successfully.

You can use this to opt out some components from rendering on the server. To do this, throw an error in the server environment and then wrap them in a <Suspense> boundary to replace their HTML with fallbacks:

<Suspense fallback={<Loading />}>

  <Chat />

</Suspense>

function Chat() {

  if (typeof window === &#x27;undefined&#x27;) {

    throw Error(&#x27;Chat should only render on the client.&#x27;);

  }

  // ...

}

The server HTML will include the loading indicator. It will be replaced by the Chat component on the client.

Troubleshooting

How do I prevent the UI from being replaced by a fallback during an update?

Replacing visible UI with a fallback creates a jarring user experience. This can happen when an update causes a component to suspend, and the nearest Suspense boundary is already showing content to the user.

To prevent this from happening, mark the update as non-urgent using startTransition. During a Transition, React will wait until enough data has loaded to prevent an unwanted fallback from appearing:

function handleNextPageClick() {

  // If this update suspends, don&#x27;t hide the already displayed content

  startTransition(() => {

    setCurrentPage(currentPage + 1);

  });

}

This will avoid hiding existing content. However, any newly rendered Suspense boundaries will still immediately display fallbacks to avoid blocking the UI and let the user see the content as it becomes available.

React will only prevent unwanted fallbacks during non-urgent updates. It will not delay a render if it’s the result of an urgent update. You must opt in with an API like startTransition or useDeferredValue.

If your router is integrated with Suspense, it should wrap its updates into startTransition automatically.

Previous<StrictMode>
Next<Activity>
