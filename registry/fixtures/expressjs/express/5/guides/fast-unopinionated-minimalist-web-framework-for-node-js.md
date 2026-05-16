# Fast, unopinionated, minimalist web framework for Node.js

**Source:** https://expressjs.com/fr/

Express - Node.js web application framework

This document might be outdated relative to the documentation in English. For the latest updates, please refer to the documentation in english.

✖

        Express5.2.1

        Fast, unopinionated, minimalist web framework for Node.js

    $ npm install express --save

    const express = require('express')
const app = express()
const port = 3000

app.get('/', (req, res) => {
  res.send('Hello World!')
})

app.listen(port, () => {
  console.log(`Example app listening on port ${port}`)
})

       [email&#160;protected]: Now the Default on npm with LTS Timeline

        Express 5.1.0 is now the default on npm, and we’re introducing an official LTS schedule for the v4 and v5 release lines. Check out our latest blog for more information.

      Web Applications
 Express is a minimal and flexible Node.js web application framework that provides a robust set of features for web and mobile applications.

      APIs
 With a myriad of HTTP utility methods and middleware at your disposal, creating a robust API is quick and easy.

      Performance
 Express provides a thin layer of fundamental web application features, without obscuring Node.js features that you know and love.

      Middleware

      Express is a lightweight and flexible routing framework with minimal core features
      meant to be augmented through the use of Express middleware modules.
