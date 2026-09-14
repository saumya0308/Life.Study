import { pgTable, text, serial, integer, timestamp, uniqueIndex } from "drizzle-orm/pg-core";

export const mistakesTable = pgTable(
  "mistakes",
  {
    id: serial("id").primaryKey(),
    studentId: integer("student_id").notNull(),
    concept: text("concept").notNull(),
    count: integer("count").notNull().default(1),
    lastMissedAt: timestamp("last_missed_at", { withTimezone: true }).notNull().defaultNow(),
  },
  (t) => [uniqueIndex("mistakes_student_concept_idx").on(t.studentId, t.concept)]
);

export type Mistake = typeof mistakesTable.$inferSelect;
