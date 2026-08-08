import React, { createContext, useContext, useMemo, useState } from "react";
import { Card } from "./cards";

type Session = {
  cards: Card[];
  hint: string;
};

type StudyContextValue = {
  session: Session;
  setSession: (session: Session) => void;
};

const StudyContext = createContext<StudyContextValue | null>(null);

export function StudyProvider({ children }: { children: React.ReactNode }) {
  const [session, setSession] = useState<Session>({ cards: [], hint: "" });
  const value = useMemo(() => ({ session, setSession }), [session]);
  return (
    <StudyContext.Provider value={value}>{children}</StudyContext.Provider>
  );
}

export function useStudySession() {
  const ctx = useContext(StudyContext);
  if (!ctx) throw new Error("useStudySession hors StudyProvider");
  return ctx;
}
