# $state

**Source:** https://svelte.dev/docs/svelte/$state

$state • Svelte Docs

  Skip to main content
TutorialPackagesPlaygroundBlog

   On this page
  The $state rune allows you to create reactive state, which means that your UI reacts when it changes.

&#x3C;script>
	let count = $state(0);
&#x3C;/script>

&#x3C;button onclick={() => count++}>
	clicks: {count}
&#x3C;/button>
Unlike other frameworks you may have encountered, there is no API for interacting with state — count is just a number, rather than an object or a function, and you can update it like you would update any other variable.

Deep state
If $state is used with an array or a simple object, the result is a deeply reactive state proxy. Proxies allow Svelte to run code when you read or write properties, including via methods like array.push(...), triggering granular updates.

State is proxified recursively until Svelte finds something other than an array or simple object (like a class or an object created with Object.create). In a case like this...

let let todos: {
    done: boolean;
    text: string;
}[]todos = function $state&#x3C;{
    done: boolean;
    text: string;
}[]>(initial: {
    done: boolean;
    text: string;
}[]): {
    done: boolean;
    text: string;
}[] (+1 overload)
namespace $stateDeclares reactive state.

Example:

let count = $state(0);

@see
{@link https://svelte.dev/docs/svelte/$state Documentation}
@param
initial The initial value

$state([
	{
		done: booleandone: false,
		text: stringtext: 'add more todos'
	}
]);
...modifying an individual todo&#39;s property will trigger updates to anything in your UI that depends on that specific property:

module todos
let todos: {
    done: boolean;
    text: string;
}[]todos[0].done: booleandone = !module todos
let todos: {
    done: boolean;
    text: string;
}[]todos[0].done: booleandone;
If you push a new object to the array, it will also be proxified:

let todos: {
    done: boolean;
    text: string;
}[]todos.Array&#x3C;{ done: boolean; text: string; }>.push(...items: {
    done: boolean;
    text: string;
}[]): numberAppends new elements to the end of an array, and returns the new length of the array.

@param
items New elements to add to the array.

push({
	done: booleandone: false,
	text: stringtext: 'eat lunch'
});
 When you update properties of proxies, the original object is not mutated. If you need to use your own proxy handlers in a state proxy, you should wrap the object after wrapping it in $state.

Note that if you destructure a reactive value, the references are not reactive — as in normal JavaScript, they are evaluated at the point of destructuring:

let { let done: booleandone, let text: stringtext } = module todos
let todos: {
    done: boolean;
    text: string;
}[]todos[0];

// this will not affect the value of `done`
module todos
let todos: {
    done: boolean;
    text: string;
}[]todos[0].done: booleandone = !module todos
let todos: {
    done: boolean;
    text: string;
}[]todos[0].done: booleandone;
Classes
Class instances are not proxied. Instead, you can use $state in class fields (whether public or private), or as the first assignment to a property immediately inside the constructor:

class class TodoTodo {
	Todo.done: booleandone = function $state&#x3C;false>(initial: false): false (+1 overload)
namespace $stateDeclares reactive state.

Example:

let count = $state(0);

@see
{@link https://svelte.dev/docs/svelte/$state Documentation}
@param
initial The initial value

$state(false);

	constructor(text) {
		this.Todo.text: anytext = function $state&#x3C;any>(initial: any): any (+1 overload)
namespace $stateDeclares reactive state.

Example:

let count = $state(0);

@see
{@link https://svelte.dev/docs/svelte/$state Documentation}
@param
initial The initial value

$state(text: anytext);
	}

	Todo.reset(): voidreset() {
		this.Todo.text: anytext = '';
		this.Todo.done: booleandone = false;
	}
}
 The compiler transforms done and text into get / set methods on the class prototype referencing private fields. This means the properties are not enumerable.

When calling methods in JavaScript, the value of this matters. This won&#39;t work, because this inside the reset method will be the <button> rather than the Todo:

&#x3C;button onclick={todo.reset}>
	reset
&#x3C;/button>
You can either use an inline function...

&#x3C;button onclick={() => todo.reset()}>
	reset
&#x3C;/button>
...or use an arrow function in the class definition:

class class TodoTodo {
	Todo.done: booleandone = function $state&#x3C;false>(initial: false): false (+1 overload)
namespace $stateDeclares reactive state.

Example:

let count = $state(0);

@see
{@link https://svelte.dev/docs/svelte/$state Documentation}
@param
initial The initial value

$state(false);

	constructor(text) {
		this.Todo.text: anytext = function $state&#x3C;any>(initial: any): any (+1 overload)
namespace $stateDeclares reactive state.

Example:

let count = $state(0);

@see
{@link https://svelte.dev/docs/svelte/$state Documentation}
@param
initial The initial value

$state(text: anytext);
	}

	Todo.reset: () => voidreset = () => {
		this.Todo.text: anytext = '';
		this.Todo.done: booleandone = false;
	}
}
Built-in classes
Svelte provides reactive implementations of built-in classes like Set, Map, Date and URL that can be imported from svelte/reactivity.

$state.raw
In cases where you don&#39;t want objects and arrays to be deeply reactive you can use $state.raw.

State declared with $state.raw cannot be mutated; it can only be reassigned. In other words, rather than assigning to a property of an object, or using an array method like push, replace the object or array altogether if you&#39;d like to update it:

let let person: {
    name: string;
    age: number;
}person = namespace $state
function $state&#x3C;T>(initial: T): T (+1 overload)Declares reactive state.

Example:

let count = $state(0);

@see
{@link https://svelte.dev/docs/svelte/$state Documentation}
@param
initial The initial value

$state.function $state.raw&#x3C;{
    name: string;
    age: number;
}>(initial: {
    name: string;
    age: number;
}): {
    name: string;
    age: number;
} (+1 overload)Declares state that is not made deeply reactive — instead of mutating it,
you must reassign it.

Example:

&#x3C;script>
  let items = $state.raw([0]);

  const addItem = () => {
	items = [...items, items.length];
  };
&#x3C;/script>

&#x3C;button onclick={addItem}>
  {items.join(', ')}
&#x3C;/button>

@see
{@link https://svelte.dev/docs/svelte/$state#$state.raw Documentation}
@param
initial The initial value

raw({
	name: stringname: 'Heraclitus',
	age: numberage: 49
});

// this will have no effect
let person: {
    name: string;
    age: number;
}person.age: numberage += 1;

// this will work, because we're creating a new person
let person: {
    name: string;
    age: number;
}person = {
	name: stringname: 'Heraclitus',
	age: numberage: 50
};
This can improve performance with large arrays and objects that you weren&#39;t planning to mutate anyway, since it avoids the cost of making them reactive. Note that raw state can contain reactive state (for example, a raw array of reactive objects).

As with $state, you can declare class fields using $state.raw.

$state.snapshot
To take a static snapshot of a deeply reactive $state proxy, use $state.snapshot:

&#x3C;script>
	let counter = $state({ count: 0 });

	function onclick() {
		// Will log `{ count: ... }` rather than `Proxy { ... }`
		console.log($state.snapshot(counter));
	}
&#x3C;/script>
This is handy when you want to pass some state to an external library or API that doesn&#39;t expect a proxy, such as structuredClone.

If a value has a toJSON method, the snapshot will clone the value returned from toJSON instead of the original object.

$state.eager
When state changes, it may not be reflected in the UI immediately if it is used by an await expression, because updates are synchronized.

In some cases, you may want to update the UI as soon as the state changes. For example, you might want to update a navigation bar when the user clicks on a link, so that they get visual feedback while waiting for the new page to load. To do this, use $state.eager(value):

&#x3C;nav>
	&#x3C;a href="/" aria-current={$state.eager(pathname) === '/' ? 'page' : null}>home&#x3C;/a>
	&#x3C;a href="/about" aria-current={$state.eager(pathname) === '/about' ? 'page' : null}>about&#x3C;/a>
&#x3C;/nav>
Use this feature sparingly, and only to provide feedback in response to user action — in general, allowing Svelte to coordinate updates will provide a better user experience.

Passing state into functions
JavaScript is a pass-by-value language — when you call a function, the arguments are the values rather than the variables. In other words:

index
/**
 * @param {number} a
 * @param {number} b
 */
function function add(a: number, b: number): number@param
a
@param
b

add(a: number@param
a

a, b: number@param
b

b) {
	return a: number@param
a

a + b: number@param
b

b;
}

let let a: numbera = 1;
let let b: numberb = 2;
let let total: numbertotal = function add(a: number, b: number): number@param
a
@param
b

add(let a: numbera, let b: numberb);
var console: ConsoleThe console module provides a simple debugging console that is similar to the
JavaScript console mechanism provided by web browsers.

The module exports two specific components:

A Console class with methods such as console.log(), console.error() and console.warn() that can be used to write to any Node.js stream.

A global console instance configured to write to process.stdout and
process.stderr. The global console can be used without importing the node:console module.

Warning: The global console object&#39;s methods are neither consistently
synchronous like the browser APIs they resemble, nor are they consistently
asynchronous like all other Node.js streams. See the note on process I/O for
more information.

Example using the global console:

console.log('hello world');
// Prints: hello world, to stdout
console.log('hello %s', 'world');
// Prints: hello world, to stdout
console.error(new Error('Whoops, something bad happened'));
// Prints error message and stack trace to stderr:
//   Error: Whoops, something bad happened
//     at [eval]:5:15
//     at Script.runInThisContext (node:vm:132:18)
//     at Object.runInThisContext (node:vm:309:38)
//     at node:internal/process/execution:77:19
//     at [eval]-wrapper:6:22
//     at evalScript (node:internal/process/execution:76:60)
//     at node:internal/main/eval_string:23:3

const name = 'Will Robinson';
console.warn(`Danger ${name}! Danger!`);
// Prints: Danger Will Robinson! Danger!, to stderr
Example using the Console class:

const out = getStreamSomehow();
const err = getStreamSomehow();
const myConsole = new console.Console(out, err);

myConsole.log('hello world');
// Prints: hello world, to out
myConsole.log('hello %s', 'world');
// Prints: hello world, to out
myConsole.error(new Error('Whoops, something bad happened'));
// Prints: [Error: Whoops, something bad happened], to err

const name = 'Will Robinson';
myConsole.warn(`Danger ${name}! Danger!`);
// Prints: Danger Will Robinson! Danger!, to err

@see
source

console.Console.log(message?: any, ...optionalParams: any[]): void (+1 overload)Prints to stdout with newline. Multiple arguments can be passed, with the
first used as the primary message and all additional used as substitution
values similar to printf(3)
(the arguments are all passed to util.format()).

const count = 5;
console.log('count: %d', count);
// Prints: count: 5, to stdout
console.log('count:', count);
// Prints: count: 5, to stdout
See util.format() for more information.

@since
v0.1.100

log(let total: numbertotal); // 3

let a: numbera = 3;
let b: numberb = 4;
var console: ConsoleThe console module provides a simple debugging console that is similar to the
JavaScript console mechanism provided by web browsers.

The module exports two specific components:

A Console class with methods such as console.log(), console.error() and console.warn() that can be used to write to any Node.js stream.

A global console instance configured to write to process.stdout and
process.stderr. The global console can be used without importing the node:console module.

Warning: The global console object&#39;s methods are neither consistently
synchronous like the browser APIs they resemble, nor are they consistently
asynchronous like all other Node.js streams. See the note on process I/O for
more information.

Example using the global console:

console.log('hello world');
// Prints: hello world, to stdout
console.log('hello %s', 'world');
// Prints: hello world, to stdout
console.error(new Error('Whoops, something bad happened'));
// Prints error message and stack trace to stderr:
//   Error: Whoops, something bad happened
//     at [eval]:5:15
//     at Script.runInThisContext (node:vm:132:18)
//     at Object.runInThisContext (node:vm:309:38)
//     at node:internal/process/execution:77:19
//     at [eval]-wrapper:6:22
//     at evalScript (node:internal/process/execution:76:60)
//     at node:internal/main/eval_string:23:3

const name = 'Will Robinson';
console.warn(`Danger ${name}! Danger!`);
// Prints: Danger Will Robinson! Danger!, to stderr
Example using the Console class:

const out = getStreamSomehow();
const err = getStreamSomehow();
const myConsole = new console.Console(out, err);

myConsole.log('hello world');
// Prints: hello world, to out
myConsole.log('hello %s', 'world');
// Prints: hello world, to out
myConsole.error(new Error('Whoops, something bad happened'));
// Prints: [Error: Whoops, something bad happened], to err

const name = 'Will Robinson';
myConsole.warn(`Danger ${name}! Danger!`);
// Prints: Danger Will Robinson! Danger!, to err

@see
source

console.Console.log(message?: any, ...optionalParams: any[]): void (+1 overload)Prints to stdout with newline. Multiple arguments can be passed, with the
first used as the primary message and all additional used as substitution
values similar to printf(3)
(the arguments are all passed to util.format()).

const count = 5;
console.log('count: %d', count);
// Prints: count: 5, to stdout
console.log('count:', count);
// Prints: count: 5, to stdout
See util.format() for more information.

@since
v0.1.100

log(let total: numbertotal); // still 3!function function add(a: number, b: number): numberadd(a: numbera: number, b: numberb: number) {
	return a: numbera + b: numberb;
}

let let a: numbera = 1;
let let b: numberb = 2;
let let total: numbertotal = function add(a: number, b: number): numberadd(let a: numbera, let b: numberb);
var console: ConsoleThe console module provides a simple debugging console that is similar to the
JavaScript console mechanism provided by web browsers.

The module exports two specific components:

A Console class with methods such as console.log(), console.error() and console.warn() that can be used to write to any Node.js stream.

A global console instance configured to write to process.stdout and
process.stderr. The global console can be used without importing the node:console module.

Warning: The global console object&#39;s methods are neither consistently
synchronous like the browser APIs they resemble, nor are they consistently
asynchronous like all other Node.js streams. See the note on process I/O for
more information.

Example using the global console:

console.log('hello world');
// Prints: hello world, to stdout
console.log('hello %s', 'world');
// Prints: hello world, to stdout
console.error(new Error('Whoops, something bad happened'));
// Prints error message and stack trace to stderr:
//   Error: Whoops, something bad happened
//     at [eval]:5:15
//     at Script.runInThisContext (node:vm:132:18)
//     at Object.runInThisContext (node:vm:309:38)
//     at node:internal/process/execution:77:19
//     at [eval]-wrapper:6:22
//     at evalScript (node:internal/process/execution:76:60)
//     at node:internal/main/eval_string:23:3

const name = 'Will Robinson';
console.warn(`Danger ${name}! Danger!`);
// Prints: Danger Will Robinson! Danger!, to stderr
Example using the Console class:

const out = getStreamSomehow();
const err = getStreamSomehow();
const myConsole = new console.Console(out, err);

myConsole.log('hello world');
// Prints: hello world, to out
myConsole.log('hello %s', 'world');
// Prints: hello world, to out
myConsole.error(new Error('Whoops, something bad happened'));
// Prints: [Error: Whoops, something bad happened], to err

const name = 'Will Robinson';
myConsole.warn(`Danger ${name}! Danger!`);
// Prints: Danger Will Robinson! Danger!, to err

@see
source

console.Console.log(message?: any, ...optionalParams: any[]): void (+1 overload)Prints to stdout with newline. Multiple arguments can be passed, with the
first used as the primary message and all additional used as substitution
values similar to printf(3)
(the arguments are all passed to util.format()).

const count = 5;
console.log('count: %d', count);
// Prints: count: 5, to stdout
console.log('count:', count);
// Prints: count: 5, to stdout
See util.format() for more information.

@since
v0.1.100

log(let total: numbertotal); // 3

let a: numbera = 3;
let b: numberb = 4;
var console: ConsoleThe console module provides a simple debugging console that is similar to the
JavaScript console mechanism provided by web browsers.

The module exports two specific components:

A Console class with methods such as console.log(), console.error() and console.warn() that can be used to write to any Node.js stream.

A global console instance configured to write to process.stdout and
process.stderr. The global console can be used without importing the node:console module.

Warning: The global console object&#39;s methods are neither consistently
synchronous like the browser APIs they resemble, nor are they consistently
asynchronous like all other Node.js streams. See the note on process I/O for
more information.

Example using the global console:

console.log('hello world');
// Prints: hello world, to stdout
console.log('hello %s', 'world');
// Prints: hello world, to stdout
console.error(new Error('Whoops, something bad happened'));
// Prints error message and stack trace to stderr:
//   Error: Whoops, something bad happened
//     at [eval]:5:15
//     at Script.runInThisContext (node:vm:132:18)
//     at Object.runInThisContext (node:vm:309:38)
//     at node:internal/process/execution:77:19
//     at [eval]-wrapper:6:22
//     at evalScript (node:internal/process/execution:76:60)
//     at node:internal/main/eval_string:23:3

const name = 'Will Robinson';
console.warn(`Danger ${name}! Danger!`);
// Prints: Danger Will Robinson! Danger!, to stderr
Example using the Console class:

const out = getStreamSomehow();
const err = getStreamSomehow();
const myConsole = new console.Console(out, err);

myConsole.log('hello world');
// Prints: hello world, to out
myConsole.log('hello %s', 'world');
// Prints: hello world, to out
myConsole.error(new Error('Whoops, something bad happened'));
// Prints: [Error: Whoops, something bad happened], to err

const name = 'Will Robinson';
myConsole.warn(`Danger ${name}! Danger!`);
// Prints: Danger Will Robinson! Danger!, to err

@see
source

console.Console.log(message?: any, ...optionalParams: any[]): void (+1 overload)Prints to stdout with newline. Multiple arguments can be passed, with the
first used as the primary message and all additional used as substitution
values similar to printf(3)
(the arguments are all passed to util.format()).

const count = 5;
console.log('count: %d', count);
// Prints: count: 5, to stdout
console.log('count:', count);
// Prints: count: 5, to stdout
See util.format() for more information.

@since
v0.1.100

log(let total: numbertotal); // still 3!
If add wanted to have access to the current values of a and b, and to return the current total value, you would need to use functions instead:

index
/**
 * @param {() => number} getA
 * @param {() => number} getB
 */
function function add(getA: () => number, getB: () => number): () => number@param
getA
@param
getB

add(getA: () => number@param
getA

getA, getB: () => number@param
getB

getB) {
	return () => getA: () => number@param
getA

getA() + getB: () => number@param
getB

getB();
}

let let a: numbera = 1;
let let b: numberb = 2;
let let total: () => numbertotal = function add(getA: () => number, getB: () => number): () => number@param
getA
@param
getB

add(() => let a: numbera, () => let b: numberb);
var console: ConsoleThe console module provides a simple debugging console that is similar to the
JavaScript console mechanism provided by web browsers.

The module exports two specific components:

A Console class with methods such as console.log(), console.error() and console.warn() that can be used to write to any Node.js stream.

A global console instance configured to write to process.stdout and
process.stderr. The global console can be used without importing the node:console module.

Warning: The global console object&#39;s methods are neither consistently
synchronous like the browser APIs they resemble, nor are they consistently
asynchronous like all other Node.js streams. See the note on process I/O for
more information.

Example using the global console:

console.log('hello world');
// Prints: hello world, to stdout
console.log('hello %s', 'world');
// Prints: hello world, to stdout
console.error(new Error('Whoops, something bad happened'));
// Prints error message and stack trace to stderr:
//   Error: Whoops, something bad happened
//     at [eval]:5:15
//     at Script.runInThisContext (node:vm:132:18)
//     at Object.runInThisContext (node:vm:309:38)
//     at node:internal/process/execution:77:19
//     at [eval]-wrapper:6:22
//     at evalScript (node:internal/process/execution:76:60)
//     at node:internal/main/eval_string:23:3

const name = 'Will Robinson';
console.warn(`Danger ${name}! Danger!`);
// Prints: Danger Will Robinson! Danger!, to stderr
Example using the Console class:

const out = getStreamSomehow();
const err = getStreamSomehow();
const myConsole = new console.Console(out, err);

myConsole.log('hello world');
// Prints: hello world, to out
myConsole.log('hello %s', 'world');
// Prints: hello world, to out
myConsole.error(new Error('Whoops, something bad happened'));
// Prints: [Error: Whoops, something bad happened], to err

const name = 'Will Robinson';
myConsole.warn(`Danger ${name}! Danger!`);
// Prints: Danger Will Robinson! Danger!, to err

@see
source

console.Console.log(message?: any, ...optionalParams: any[]): void (+1 overload)Prints to stdout with newline. Multiple arguments can be passed, with the
first used as the primary message and all additional used as substitution
values similar to printf(3)
(the arguments are all passed to util.format()).

const count = 5;
console.log('count: %d', count);
// Prints: count: 5, to stdout
console.log('count:', count);
// Prints: count: 5, to stdout
See util.format() for more information.

@since
v0.1.100

log(let total: () => numbertotal()); // 3

let a: numbera = 3;
let b: numberb = 4;
var console: ConsoleThe console module provides a simple debugging console that is similar to the
JavaScript console mechanism provided by web browsers.

The module exports two specific components:

A Console class with methods such as console.log(), console.error() and console.warn() that can be used to write to any Node.js stream.

A global console instance configured to write to process.stdout and
process.stderr. The global console can be used without importing the node:console module.

Warning: The global console object&#39;s methods are neither consistently
synchronous like the browser APIs they resemble, nor are they consistently
asynchronous like all other Node.js streams. See the note on process I/O for
more information.

Example using the global console:

console.log('hello world');
// Prints: hello world, to stdout
console.log('hello %s', 'world');
// Prints: hello world, to stdout
console.error(new Error('Whoops, something bad happened'));
// Prints error message and stack trace to stderr:
//   Error: Whoops, something bad happened
//     at [eval]:5:15
//     at Script.runInThisContext (node:vm:132:18)
//     at Object.runInThisContext (node:vm:309:38)
//     at node:internal/process/execution:77:19
//     at [eval]-wrapper:6:22
//     at evalScript (node:internal/process/execution:76:60)
//     at node:internal/main/eval_string:23:3

const name = 'Will Robinson';
console.warn(`Danger ${name}! Danger!`);
// Prints: Danger Will Robinson! Danger!, to stderr
Example using the Console class:

const out = getStreamSomehow();
const err = getStreamSomehow();
const myConsole = new console.Console(out, err);

myConsole.log('hello world');
// Prints: hello world, to out
myConsole.log('hello %s', 'world');
// Prints: hello world, to out
myConsole.error(new Error('Whoops, something bad happened'));
// Prints: [Error: Whoops, something bad happened], to err

const name = 'Will Robinson';
myConsole.warn(`Danger ${name}! Danger!`);
// Prints: Danger Will Robinson! Danger!, to err

@see
source

console.Console.log(message?: any, ...optionalParams: any[]): void (+1 overload)Prints to stdout with newline. Multiple arguments can be passed, with the
first used as the primary message and all additional used as substitution
values similar to printf(3)
(the arguments are all passed to util.format()).

const count = 5;
console.log('count: %d', count);
// Prints: count: 5, to stdout
console.log('count:', count);
// Prints: count: 5, to stdout
See util.format() for more information.

@since
v0.1.100

log(let total: () => numbertotal()); // 7function function add(getA: () => number, getB: () => number): () => numberadd(getA: () => numbergetA: () => number, getB: () => numbergetB: () => number) {
	return () => getA: () => numbergetA() + getB: () => numbergetB();
}

let let a: numbera = 1;
let let b: numberb = 2;
let let total: () => numbertotal = function add(getA: () => number, getB: () => number): () => numberadd(() => let a: numbera, () => let b: numberb);
var console: ConsoleThe console module provides a simple debugging console that is similar to the
JavaScript console mechanism provided by web browsers.

The module exports two specific components:

A Console class with methods such as console.log(), console.error() and console.warn() that can be used to write to any Node.js stream.

A global console instance configured to write to process.stdout and
process.stderr. The global console can be used without importing the node:console module.

Warning: The global console object&#39;s methods are neither consistently
synchronous like the browser APIs they resemble, nor are they consistently
asynchronous like all other Node.js streams. See the note on process I/O for
more information.

Example using the global console:

console.log('hello world');
// Prints: hello world, to stdout
console.log('hello %s', 'world');
// Prints: hello world, to stdout
console.error(new Error('Whoops, something bad happened'));
// Prints error message and stack trace to stderr:
//   Error: Whoops, something bad happened
//     at [eval]:5:15
//     at Script.runInThisContext (node:vm:132:18)
//     at Object.runInThisContext (node:vm:309:38)
//     at node:internal/process/execution:77:19
//     at [eval]-wrapper:6:22
//     at evalScript (node:internal/process/execution:76:60)
//     at node:internal/main/eval_string:23:3

const name = 'Will Robinson';
console.warn(`Danger ${name}! Danger!`);
// Prints: Danger Will Robinson! Danger!, to stderr
Example using the Console class:

const out = getStreamSomehow();
const err = getStreamSomehow();
const myConsole = new console.Console(out, err);

myConsole.log('hello world');
// Prints: hello world, to out
myConsole.log('hello %s', 'world');
// Prints: hello world, to out
myConsole.error(new Error('Whoops, something bad happened'));
// Prints: [Error: Whoops, something bad happened], to err

const name = 'Will Robinson';
myConsole.warn(`Danger ${name}! Danger!`);
// Prints: Danger Will Robinson! Danger!, to err

@see
source

console.Console.log(message?: any, ...optionalParams: any[]): void (+1 overload)Prints to stdout with newline. Multiple arguments can be passed, with the
first used as the primary message and all additional used as substitution
values similar to printf(3)
(the arguments are all passed to util.format()).

const count = 5;
console.log('count: %d', count);
// Prints: count: 5, to stdout
console.log('count:', count);
// Prints: count: 5, to stdout
See util.format() for more information.

@since
v0.1.100

log(let total: () => numbertotal()); // 3

let a: numbera = 3;
let b: numberb = 4;
var console: ConsoleThe console module provides a simple debugging console that is similar to the
JavaScript console mechanism provided by web browsers.

The module exports two specific components:

A Console class with methods such as console.log(), console.error() and console.warn() that can be used to write to any Node.js stream.

A global console instance configured to write to process.stdout and
process.stderr. The global console can be used without importing the node:console module.

Warning: The global console object&#39;s methods are neither consistently
synchronous like the browser APIs they resemble, nor are they consistently
asynchronous like all other Node.js streams. See the note on process I/O for
more information.

Example using the global console:

console.log('hello world');
// Prints: hello world, to stdout
console.log('hello %s', 'world');
// Prints: hello world, to stdout
console.error(new Error('Whoops, something bad happened'));
// Prints error message and stack trace to stderr:
//   Error: Whoops, something bad happened
//     at [eval]:5:15
//     at Script.runInThisContext (node:vm:132:18)
//     at Object.runInThisContext (node:vm:309:38)
//     at node:internal/process/execution:77:19
//     at [eval]-wrapper:6:22
//     at evalScript (node:internal/process/execution:76:60)
//     at node:internal/main/eval_string:23:3

const name = 'Will Robinson';
console.warn(`Danger ${name}! Danger!`);
// Prints: Danger Will Robinson! Danger!, to stderr
Example using the Console class:

const out = getStreamSomehow();
const err = getStreamSomehow();
const myConsole = new console.Console(out, err);

myConsole.log('hello world');
// Prints: hello world, to out
myConsole.log('hello %s', 'world');
// Prints: hello world, to out
myConsole.error(new Error('Whoops, something bad happened'));
// Prints: [Error: Whoops, something bad happened], to err

const name = 'Will Robinson';
myConsole.warn(`Danger ${name}! Danger!`);
// Prints: Danger Will Robinson! Danger!, to err

@see
source

console.Console.log(message?: any, ...optionalParams: any[]): void (+1 overload)Prints to stdout with newline. Multiple arguments can be passed, with the
first used as the primary message and all additional used as substitution
values similar to printf(3)
(the arguments are all passed to util.format()).

const count = 5;
console.log('count: %d', count);
// Prints: count: 5, to stdout
console.log('count:', count);
// Prints: count: 5, to stdout
See util.format() for more information.

@since
v0.1.100

log(let total: () => numbertotal()); // 7
State in Svelte is no different — when you reference something declared with the $state rune...

let let a: numbera = function $state&#x3C;1>(initial: 1): 1 (+1 overload)
namespace $stateDeclares reactive state.

Example:

let count = $state(0);

@see
{@link https://svelte.dev/docs/svelte/$state Documentation}
@param
initial The initial value

$state(1);
let let b: numberb = function $state&#x3C;2>(initial: 2): 2 (+1 overload)
namespace $stateDeclares reactive state.

Example:

let count = $state(0);

@see
{@link https://svelte.dev/docs/svelte/$state Documentation}
@param
initial The initial value

$state(2);
...you&#39;re accessing its current value.

Note that &#39;functions&#39; is broad — it encompasses properties of proxies and get/set properties...

index
/**
 * @param {{ a: number, b: number }} input
 */
function function add(input: {
    a: number;
    b: number;
}): {
    readonly value: number;
}@param
input

add(input: {
    a: number;
    b: number;
}@param
input

input) {
	return {
		get value: numbervalue() {
			return input: {
    a: number;
    b: number;
}@param
input

input.a: numbera + input: {
    a: number;
    b: number;
}@param
input

input.b: numberb;
		}
	};
}

let module input
let input: {
    a: number;
    b: number;
}input = function $state&#x3C;{
    a: number;
    b: number;
}>(initial: {
    a: number;
    b: number;
}): {
    a: number;
    b: number;
} (+1 overload)
namespace $stateDeclares reactive state.

Example:

let count = $state(0);

@see
{@link https://svelte.dev/docs/svelte/$state Documentation}
@param
initial The initial value

$state({ a: numbera: 1, b: numberb: 2 });
let let total: {
    readonly value: number;
}total = function add(input: {
    a: number;
    b: number;
}): {
    readonly value: number;
}@param
input

add(module input
let input: {
    a: number;
    b: number;
}input);
var console: ConsoleThe console module provides a simple debugging console that is similar to the
JavaScript console mechanism provided by web browsers.

The module exports two specific components:

A Console class with methods such as console.log(), console.error() and console.warn() that can be used to write to any Node.js stream.

A global console instance configured to write to process.stdout and
process.stderr. The global console can be used without importing the node:console module.

Warning: The global console object&#39;s methods are neither consistently
synchronous like the browser APIs they resemble, nor are they consistently
asynchronous like all other Node.js streams. See the note on process I/O for
more information.

Example using the global console:

console.log('hello world');
// Prints: hello world, to stdout
console.log('hello %s', 'world');
// Prints: hello world, to stdout
console.error(new Error('Whoops, something bad happened'));
// Prints error message and stack trace to stderr:
//   Error: Whoops, something bad happened
//     at [eval]:5:15
//     at Script.runInThisContext (node:vm:132:18)
//     at Object.runInThisContext (node:vm:309:38)
//     at node:internal/process/execution:77:19
//     at [eval]-wrapper:6:22
//     at evalScript (node:internal/process/execution:76:60)
//     at node:internal/main/eval_string:23:3

const name = 'Will Robinson';
console.warn(`Danger ${name}! Danger!`);
// Prints: Danger Will Robinson! Danger!, to stderr
Example using the Console class:

const out = getStreamSomehow();
const err = getStreamSomehow();
const myConsole = new console.Console(out, err);

myConsole.log('hello world');
// Prints: hello world, to out
myConsole.log('hello %s', 'world');
// Prints: hello world, to out
myConsole.error(new Error('Whoops, something bad happened'));
// Prints: [Error: Whoops, something bad happened], to err

const name = 'Will Robinson';
myConsole.warn(`Danger ${name}! Danger!`);
// Prints: Danger Will Robinson! Danger!, to err

@see
source

console.Console.log(message?: any, ...optionalParams: any[]): void (+1 overload)Prints to stdout with newline. Multiple arguments can be passed, with the
first used as the primary message and all additional used as substitution
values similar to printf(3)
(the arguments are all passed to util.format()).

const count = 5;
console.log('count: %d', count);
// Prints: count: 5, to stdout
console.log('count:', count);
// Prints: count: 5, to stdout
See util.format() for more information.

@since
v0.1.100

log(let total: {
    readonly value: number;
}total.value: numbervalue); // 3

module input
let input: {
    a: number;
    b: number;
}input.a: numbera = 3;
module input
let input: {
    a: number;
    b: number;
}input.b: numberb = 4;
var console: ConsoleThe console module provides a simple debugging console that is similar to the
JavaScript console mechanism provided by web browsers.

The module exports two specific components:

A Console class with methods such as console.log(), console.error() and console.warn() that can be used to write to any Node.js stream.

A global console instance configured to write to process.stdout and
process.stderr. The global console can be used without importing the node:console module.

Warning: The global console object&#39;s methods are neither consistently
synchronous like the browser APIs they resemble, nor are they consistently
asynchronous like all other Node.js streams. See the note on process I/O for
more information.

Example using the global console:

console.log('hello world');
// Prints: hello world, to stdout
console.log('hello %s', 'world');
// Prints: hello world, to stdout
console.error(new Error('Whoops, something bad happened'));
// Prints error message and stack trace to stderr:
//   Error: Whoops, something bad happened
//     at [eval]:5:15
//     at Script.runInThisContext (node:vm:132:18)
//     at Object.runInThisContext (node:vm:309:38)
//     at node:internal/process/execution:77:19
//     at [eval]-wrapper:6:22
//     at evalScript (node:internal/process/execution:76:60)
//     at node:internal/main/eval_string:23:3

const name = 'Will Robinson';
console.warn(`Danger ${name}! Danger!`);
// Prints: Danger Will Robinson! Danger!, to stderr
Example using the Console class:

const out = getStreamSomehow();
const err = getStreamSomehow();
const myConsole = new console.Console(out, err);

myConsole.log('hello world');
// Prints: hello world, to out
myConsole.log('hello %s', 'world');
// Prints: hello world, to out
myConsole.error(new Error('Whoops, something bad happened'));
// Prints: [Error: Whoops, something bad happened], to err

const name = 'Will Robinson';
myConsole.warn(`Danger ${name}! Danger!`);
// Prints: Danger Will Robinson! Danger!, to err

@see
source

console.Console.log(message?: any, ...optionalParams: any[]): void (+1 overload)Prints to stdout with newline. Multiple arguments can be passed, with the
first used as the primary message and all additional used as substitution
values similar to printf(3)
(the arguments are all passed to util.format()).

const count = 5;
console.log('count: %d', count);
// Prints: count: 5, to stdout
console.log('count:', count);
// Prints: count: 5, to stdout
See util.format() for more information.

@since
v0.1.100

log(let total: {
    readonly value: number;
}total.value: numbervalue); // 7function function add(input: {
    a: number;
    b: number;
}): {
    readonly value: number;
}add(input: {
    a: number;
    b: number;
}input: { a: numbera: number, b: numberb: number }) {
	return {
		get value: numbervalue() {
			return input: {
    a: number;
    b: number;
}input.a: numbera + input: {
    a: number;
    b: number;
}input.b: numberb;
		}
	};
}

let let input: {
    a: number;
    b: number;
}input = function $state&#x3C;{
    a: number;
    b: number;
}>(initial: {
    a: number;
    b: number;
}): {
    a: number;
    b: number;
} (+1 overload)
namespace $stateDeclares reactive state.

Example:

let count = $state(0);

@see
{@link https://svelte.dev/docs/svelte/$state Documentation}
@param
initial The initial value

$state({ a: numbera: 1, b: numberb: 2 });
let let total: {
    readonly value: number;
}total = function add(input: {
    a: number;
    b: number;
}): {
    readonly value: number;
}add(let input: {
    a: number;
    b: number;
}input);
var console: ConsoleThe console module provides a simple debugging console that is similar to the
JavaScript console mechanism provided by web browsers.

The module exports two specific components:

A Console class with methods such as console.log(), console.error() and console.warn() that can be used to write to any Node.js stream.

A global console instance configured to write to process.stdout and
process.stderr. The global console can be used without importing the node:console module.

Warning: The global console object&#39;s methods are neither consistently
synchronous like the browser APIs they resemble, nor are they consistently
asynchronous like all other Node.js streams. See the note on process I/O for
more information.

Example using the global console:

console.log('hello world');
// Prints: hello world, to stdout
console.log('hello %s', 'world');
// Prints: hello world, to stdout
console.error(new Error('Whoops, something bad happened'));
// Prints error message and stack trace to stderr:
//   Error: Whoops, something bad happened
//     at [eval]:5:15
//     at Script.runInThisContext (node:vm:132:18)
//     at Object.runInThisContext (node:vm:309:38)
//     at node:internal/process/execution:77:19
//     at [eval]-wrapper:6:22
//     at evalScript (node:internal/process/execution:76:60)
//     at node:internal/main/eval_string:23:3

const name = 'Will Robinson';
console.warn(`Danger ${name}! Danger!`);
// Prints: Danger Will Robinson! Danger!, to stderr
Example using the Console class:

const out = getStreamSomehow();
const err = getStreamSomehow();
const myConsole = new console.Console(out, err);

myConsole.log('hello world');
// Prints: hello world, to out
myConsole.log('hello %s', 'world');
// Prints: hello world, to out
myConsole.error(new Error('Whoops, something bad happened'));
// Prints: [Error: Whoops, something bad happened], to err

const name = 'Will Robinson';
myConsole.warn(`Danger ${name}! Danger!`);
// Prints: Danger Will Robinson! Danger!, to err

@see
source

console.Console.log(message?: any, ...optionalParams: any[]): void (+1 overload)Prints to stdout with newline. Multiple arguments can be passed, with the
first used as the primary message and all additional used as substitution
values similar to printf(3)
(the arguments are all passed to util.format()).

const count = 5;
console.log('count: %d', count);
// Prints: count: 5, to stdout
console.log('count:', count);
// Prints: count: 5, to stdout
See util.format() for more information.

@since
v0.1.100

log(let total: {
    readonly value: number;
}total.value: numbervalue); // 3

let input: {
    a: number;
    b: number;
}input.a: numbera = 3;
let input: {
    a: number;
    b: number;
}input.b: numberb = 4;
var console: ConsoleThe console module provides a simple debugging console that is similar to the
JavaScript console mechanism provided by web browsers.

The module exports two specific components:

A Console class with methods such as console.log(), console.error() and console.warn() that can be used to write to any Node.js stream.

A global console instance configured to write to process.stdout and
process.stderr. The global console can be used without importing the node:console module.

Warning: The global console object&#39;s methods are neither consistently
synchronous like the browser APIs they resemble, nor are they consistently
asynchronous like all other Node.js streams. See the note on process I/O for
more information.

Example using the global console:

console.log('hello world');
// Prints: hello world, to stdout
console.log('hello %s', 'world');
// Prints: hello world, to stdout
console.error(new Error('Whoops, something bad happened'));
// Prints error message and stack trace to stderr:
//   Error: Whoops, something bad happened
//     at [eval]:5:15
//     at Script.runInThisContext (node:vm:132:18)
//     at Object.runInThisContext (node:vm:309:38)
//     at node:internal/process/execution:77:19
//     at [eval]-wrapper:6:22
//     at evalScript (node:internal/process/execution:76:60)
//     at node:internal/main/eval_string:23:3

const name = 'Will Robinson';
console.warn(`Danger ${name}! Danger!`);
// Prints: Danger Will Robinson! Danger!, to stderr
Example using the Console class:

const out = getStreamSomehow();
const err = getStreamSomehow();
const myConsole = new console.Console(out, err);

myConsole.log('hello world');
// Prints: hello world, to out
myConsole.log('hello %s', 'world');
// Prints: hello world, to out
myConsole.error(new Error('Whoops, something bad happened'));
// Prints: [Error: Whoops, something bad happened], to err

const name = 'Will Robinson';
myConsole.warn(`Danger ${name}! Danger!`);
// Prints: Danger Will Robinson! Danger!, to err

@see
source

console.Console.log(message?: any, ...optionalParams: any[]): void (+1 overload)Prints to stdout with newline. Multiple arguments can be passed, with the
first used as the primary message and all additional used as substitution
values similar to printf(3)
(the arguments are all passed to util.format()).

const count = 5;
console.log('count: %d', count);
// Prints: count: 5, to stdout
console.log('count:', count);
// Prints: count: 5, to stdout
See util.format() for more information.

@since
v0.1.100

log(let total: {
    readonly value: number;
}total.value: numbervalue); // 7
...though if you find yourself writing code like that, consider using classes instead.

Passing state across modules
You can declare state in .svelte.js and .svelte.ts files, but you can only export that state if it&#39;s not directly reassigned. In other words you can&#39;t do this:

state.svelte
export let let count: numbercount = function $state&#x3C;0>(initial: 0): 0 (+1 overload)
namespace $stateDeclares reactive state.

Example:

let count = $state(0);

@see
{@link https://svelte.dev/docs/svelte/$state Documentation}
@param
initial The initial value

$state(0);

export function function increment(): voidincrement() {
	let count: numbercount += 1;
}
That&#39;s because every reference to count is transformed by the Svelte compiler — the code above is roughly equivalent to this:

state.svelte
export let let count: Signal&#x3C;number>count = const $: Svelte$.Svelte.state&#x3C;number>(value?: number | undefined): Signal&#x3C;number>state(0);

export function function increment(): voidincrement() {
	const $: Svelte$.Svelte.set&#x3C;number>(source: Signal&#x3C;number>, value: number): voidset(let count: Signal&#x3C;number>count, const $: Svelte$.Svelte.get&#x3C;number>(source: Signal&#x3C;number>): numberget(let count: Signal&#x3C;number>count) + 1);
}
 You can see the code Svelte generates by clicking the &#39;JS Output&#39; tab in the playground.

Since the compiler only operates on one file at a time, if another file imports count Svelte doesn&#39;t know that it needs to wrap each reference in $.get and $.set:

import { let count: numbercount } from './state.svelte.js';

var console: ConsoleThe console module provides a simple debugging console that is similar to the
JavaScript console mechanism provided by web browsers.

The module exports two specific components:

A Console class with methods such as console.log(), console.error() and console.warn() that can be used to write to any Node.js stream.

A global console instance configured to write to process.stdout and
process.stderr. The global console can be used without importing the node:console module.

Warning: The global console object&#39;s methods are neither consistently
synchronous like the browser APIs they resemble, nor are they consistently
asynchronous like all other Node.js streams. See the note on process I/O for
more information.

Example using the global console:

console.log('hello world');
// Prints: hello world, to stdout
console.log('hello %s', 'world');
// Prints: hello world, to stdout
console.error(new Error('Whoops, something bad happened'));
// Prints error message and stack trace to stderr:
//   Error: Whoops, something bad happened
//     at [eval]:5:15
//     at Script.runInThisContext (node:vm:132:18)
//     at Object.runInThisContext (node:vm:309:38)
//     at node:internal/process/execution:77:19
//     at [eval]-wrapper:6:22
//     at evalScript (node:internal/process/execution:76:60)
//     at node:internal/main/eval_string:23:3

const name = 'Will Robinson';
console.warn(`Danger ${name}! Danger!`);
// Prints: Danger Will Robinson! Danger!, to stderr
Example using the Console class:

const out = getStreamSomehow();
const err = getStreamSomehow();
const myConsole = new console.Console(out, err);

myConsole.log('hello world');
// Prints: hello world, to out
myConsole.log('hello %s', 'world');
// Prints: hello world, to out
myConsole.error(new Error('Whoops, something bad happened'));
// Prints: [Error: Whoops, something bad happened], to err

const name = 'Will Robinson';
myConsole.warn(`Danger ${name}! Danger!`);
// Prints: Danger Will Robinson! Danger!, to err

@see
source

console.Console.log(message?: any, ...optionalParams: any[]): void (+1 overload)Prints to stdout with newline. Multiple arguments can be passed, with the
first used as the primary message and all additional used as substitution
values similar to printf(3)
(the arguments are all passed to util.format()).

const count = 5;
console.log('count: %d', count);
// Prints: count: 5, to stdout
console.log('count:', count);
// Prints: count: 5, to stdout
See util.format() for more information.

@since
v0.1.100

log(typeof let count: numbercount); // 'object', not 'number'
This leaves you with two options for sharing state between modules — either don&#39;t reassign it...

// This is allowed — since we're updating
// `counter.count` rather than `counter`,
// Svelte doesn't wrap it in `$.state`
export const const counter: {
    count: number;
}counter = function $state&#x3C;{
    count: number;
}>(initial: {
    count: number;
}): {
    count: number;
} (+1 overload)
namespace $stateDeclares reactive state.

Example:

let count = $state(0);

@see
{@link https://svelte.dev/docs/svelte/$state Documentation}
@param
initial The initial value

$state({
	count: numbercount: 0
});

export function function increment(): voidincrement() {
	const counter: {
    count: number;
}counter.count: numbercount += 1;
}
...or don&#39;t directly export it:

let let count: numbercount = function $state&#x3C;0>(initial: 0): 0 (+1 overload)
namespace $stateDeclares reactive state.

Example:

let count = $state(0);

@see
{@link https://svelte.dev/docs/svelte/$state Documentation}
@param
initial The initial value

$state(0);

export function function getCount(): numbergetCount() {
	return let count: numbercount;
}

export function function increment(): voidincrement() {
	let count: numbercount += 1;
}

  Edit this page on GitHub  llms.txt
 previous next
 What are runes? $derived
