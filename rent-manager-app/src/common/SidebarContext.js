import { createContext, useCallback, useContext, useEffect, useState } from 'react';

const SidebarContext = createContext({
  collapsed: false,
  accountOpen: false,
  toggleSidebar: () => {},
  toggleAccount: () => {},
  closeAccount: () => {},
});

export const SidebarProvider = ({ children }) => {
  const [collapsed, setCollapsed] = useState(false);
  const [accountOpen, setAccountOpen] = useState(false);

  const toggleSidebar = useCallback(() => setCollapsed((prev) => !prev), []);
  const toggleAccount = useCallback(() => setAccountOpen((prev) => !prev), []);
  const closeAccount = useCallback(() => setAccountOpen(false), []);

  useEffect(() => {
    document.body.classList.toggle('app-sidebar-collapsed', collapsed);
    window.dispatchEvent(new Event('resize'));
  }, [collapsed]);

  useEffect(() => {
    return () => {
      document.body.classList.remove('app-sidebar-collapsed');
    };
  }, []);

  return (
    <SidebarContext.Provider
      value={{ collapsed, accountOpen, toggleSidebar, toggleAccount, closeAccount }}
    >
      {children}
    </SidebarContext.Provider>
  );
};

export const useSidebar = () => useContext(SidebarContext);

export default SidebarContext;
