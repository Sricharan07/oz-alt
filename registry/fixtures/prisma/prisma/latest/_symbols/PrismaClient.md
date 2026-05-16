# PrismaClient

**Kind:** expected
**Signature:** `PrismaClient`
**Source:** https://www.prisma.io/docs/orm/prisma-client

## Example

```markdown
bun

npx prisma generate

If you want more detail on this step, see Generating Prisma Client.

4. Import and use the generated client

import { PrismaClient } from &quot;./generated/client&quot;;

const prisma = new PrismaClient();

const users = await prisma.user.findMany();

Common tasks

Set up and configure Prisma Client
```
