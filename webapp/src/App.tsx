import { CssBaseline, ThemeProvider, createTheme } from '@mui/material';
import { Route, Routes } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Configurations from './pages/Configurations';
import Projects from './pages/Projects';
import Automations from './pages/Automations';
import Collaboration from './pages/Collaboration';
import Streaming from './pages/Streaming';

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#00658a'
    },
    secondary: {
      main: '#00bcd4'
    },
    background: {
      default: '#f5f7fb',
      paper: '#ffffff'
    }
  },
  typography: {
    fontFamily: 'Inter, Roboto, Helvetica, Arial, sans-serif'
  },
  shape: {
    borderRadius: 12
  }
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/configurations" element={<Configurations />} />
          <Route path="/projects" element={<Projects />} />
          <Route path="/automations" element={<Automations />} />
          <Route path="/collaboration" element={<Collaboration />} />
          <Route path="/streaming" element={<Streaming />} />
        </Routes>
      </Layout>
    </ThemeProvider>
  );
}

export default App;
