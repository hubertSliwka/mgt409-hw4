import { createContext, useContext, useMemo, useState } from "react";
import type { ReactNode } from "react";
import type { PageContext } from "../types";

type PageValue = {
  context: PageContext;
  setContext: (next: PageContext) => void;
  draft: string;
  setDraft: (next: string) => void;
  openSignal: number;
  openChat: (prefill?: string) => void;
};

const PageContextStore = createContext<PageValue | null>(null);

export function PageContextProvider({ children }: { children: ReactNode }) {
  const [context, setContext] = useState<PageContext>({ page: "home", product_id: null });
  const [draft, setDraft] = useState("");
  const [openSignal, setOpenSignal] = useState(0);

  const value = useMemo<PageValue>(
    () => ({
      context,
      setContext,
      draft,
      setDraft,
      openSignal,
      // Bumping the signal is what tells the floating panel to open itself.
      openChat: (prefill?: string) => {
        if (prefill !== undefined) setDraft(prefill);
        setOpenSignal((count) => count + 1);
      },
    }),
    [context, draft, openSignal],
  );

  return <PageContextStore.Provider value={value}>{children}</PageContextStore.Provider>;
}

export function usePageContext(): PageValue {
  const value = useContext(PageContextStore);
  if (!value) throw new Error("usePageContext must be used inside PageContextProvider");
  return value;
}
