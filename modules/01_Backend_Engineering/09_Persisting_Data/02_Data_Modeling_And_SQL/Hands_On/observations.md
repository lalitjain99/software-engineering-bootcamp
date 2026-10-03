What happens when the duplicate SKU is inserted?

Ans: Query failed with error as Unique constraint failed

What happens when the store_id does not exist?

Ans: Query failed with error as Foreign Key constraint failed

What happens when a store with products is deleted?

Ans: Query failed with error as Foreign key constraint failed

What does the JOIN return?

Ans - Wireless Mouse (MS-901) is sold at Tech Superstore
   - Mechanical Keyboard (KB-202) is sold at Tech Superstore
   - Cotton T-Shirt (TS-505) is sold at Fashion Hub
   - Denim Jeans (DJ-404) is sold at Fashion Hub

Which errors come from the database rather than from FastAPI or Pydantic?

Ans: Duplicate SKU → unique constraint violation
Non-existent store_id during product insertion → foreign-key violation
Deleting a store that still has products → foreign-key restriction violation

What changes when PRAGMA foreign_keys = ON is removed?

Ans: SQLite parses and stores the foreign-key definition, but does not enforce it for that connection unless PRAGMA foreign_keys = ON is enabled.

Also, this setting is connection-specific. Every new SQLite connection must enable it.
With enforcement disabled:
- Invalid orphan products can be inserted.
- A store can be deleted while products still reference it.
- The schema can still be created successfully.

Key Changes in Behavior
1. Orphan Records on Insertion
With Foreign Keys ON: Trying to insert a product with a store_id that does not exist throws an IntegrityError.

With Foreign Keys OFF: SQLite will happily accept the insert. You will end up with orphan records—products referencing a store ID that doesn't exist anywhere in your database.

2. Deletion Guard Fails (ON DELETE RESTRICT Ignored)
With Foreign Keys ON: Trying to delete a store that still has products linked to it is blocked with an IntegrityError.

With Foreign Keys OFF: SQLite allows you to delete the store immediately. The products referencing that store are left behind with a dead/dangling store_id, breaking your relational integrity.

3. Does it throw a syntax error when creating tables?
No. SQLite allows you to write FOREIGN KEY constraints in your CREATE TABLE statement regardless of whether the PRAGMA is enabled or disabled. It just treats them as comments/metadata unless the PRAGMA is turned on.