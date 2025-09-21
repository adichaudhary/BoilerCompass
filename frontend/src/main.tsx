import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import Layout from './layout';
import Home from './page';

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <Layout>
      <Home />
    </Layout>
  </StrictMode>
);
