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

Ans: 1. When user try to delete a particular store whose product still exists in the product table. Query resulted in error as    Foreign key constraint failed.
     2. When user try to insert a new product into a non existant resulted in database error. Query resulted in error as Foreign key constraint failed.

What changes when PRAGMA foreign_keys = ON is removed?

Ans: When PRAGMA foreign_keys = ON; is removed (meaning it defaults to OFF), SQLite stops enforcing any relationships between your tables.

Even though your table schema explicitly defines a FOREIGN KEY clause and ON DELETE RESTRICT, SQLite will completely ignore them at runtime.

Key Changes in Behavior
1. Orphan Records on Insertion
With Foreign Keys ON: Trying to insert a product with a store_id that does not exist throws an IntegrityError.

With Foreign Keys OFF: SQLite will happily accept the insert. You will end up with orphan records—products referencing a store ID that doesn't exist anywhere in your database.

2. Deletion Guard Fails (ON DELETE RESTRICT Ignored)
With Foreign Keys ON: Trying to delete a store that still has products linked to it is blocked with an IntegrityError.

With Foreign Keys OFF: SQLite allows you to delete the store immediately. The products referencing that store are left behind with a dead/dangling store_id, breaking your relational integrity.

3. Does it throw a syntax error when creating tables?
No. SQLite allows you to write FOREIGN KEY constraints in your CREATE TABLE statement regardless of whether the PRAGMA is enabled or disabled. It just treats them as comments/metadata unless the PRAGMA is turned on.