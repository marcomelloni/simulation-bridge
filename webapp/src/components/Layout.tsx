import MenuIcon from '@mui/icons-material/Menu';
import PlayArrowRoundedIcon from '@mui/icons-material/PlayArrowRounded';
import {
  AppBar,
  Avatar,
  Box,
  Divider,
  Drawer,
  IconButton,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Toolbar,
  Typography
} from '@mui/material';
import { useMemo, useState } from 'react';
import { NavLink, useLocation, useNavigate } from 'react-router-dom';
import DashboardRoundedIcon from '@mui/icons-material/DashboardRounded';
import SettingsSuggestRoundedIcon from '@mui/icons-material/SettingsSuggestRounded';
import Inventory2RoundedIcon from '@mui/icons-material/Inventory2Rounded';
import AutomationRoundedIcon from '@mui/icons-material/PrecisionManufacturingRounded';
import GroupRoundedIcon from '@mui/icons-material/GroupsRounded';
import StreamingRoundedIcon from '@mui/icons-material/Stream';

const drawerWidth = 260;

const navItems = [
  { label: 'Dashboard', path: '/', icon: <DashboardRoundedIcon /> },
  { label: 'Configurazioni', path: '/configurations', icon: <SettingsSuggestRoundedIcon /> },
  { label: 'Progetti', path: '/projects', icon: <Inventory2RoundedIcon /> },
  { label: 'Automazioni', path: '/automations', icon: <AutomationRoundedIcon /> },
  { label: 'Collaborazione', path: '/collaboration', icon: <GroupRoundedIcon /> },
  { label: 'Streaming', path: '/streaming', icon: <StreamingRoundedIcon /> }
];

interface LayoutProps {
  children: React.ReactNode;
}

function Layout({ children }: LayoutProps) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();

  const activeLabel = useMemo(() => {
    const item = navItems.find((nav) => nav.path === location.pathname);
    return item?.label ?? 'Simulation Bridge';
  }, [location.pathname]);

  const drawer = (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <Box sx={{ p: 3 }}>
        <Typography variant="h6" fontWeight={700} color="primary">
          Simulation Bridge
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Console web per orchestrare test e integrazioni
        </Typography>
      </Box>
      <Divider />
      <List sx={{ flexGrow: 1 }}>
        {navItems.map((item) => (
          <ListItem key={item.path} disablePadding>
            <ListItemButton
              component={NavLink}
              to={item.path}
              onClick={() => setMobileOpen(false)}
              sx={{
                borderRadius: 2,
                mx: 1,
                my: 0.5,
                '&.active': {
                  backgroundColor: 'rgba(0, 101, 138, 0.12)',
                  color: 'primary.main'
                }
              }}
            >
              <ListItemIcon sx={{ color: 'inherit', minWidth: 36 }}>{item.icon}</ListItemIcon>
              <ListItemText primary={item.label} />
            </ListItemButton>
          </ListItem>
        ))}
      </List>
      <Divider />
      <Box sx={{ p: 3, display: 'flex', gap: 2, alignItems: 'center' }}>
        <Avatar sx={{ bgcolor: 'primary.main' }}>SB</Avatar>
        <Box>
          <Typography variant="subtitle2">Operatore Bridge</Typography>
          <Typography variant="caption" color="text.secondary">
            admin@simulation.bridge
          </Typography>
        </Box>
      </Box>
    </Box>
  );

  return (
    <Box sx={{ display: 'flex', height: '100vh', bgcolor: 'background.default' }}>
      <AppBar
        position="fixed"
        elevation={0}
        sx={{
          zIndex: (theme) => theme.zIndex.drawer + 1,
          bgcolor: 'background.paper',
          borderBottom: (theme) => `1px solid ${theme.palette.divider}`,
          color: 'text.primary'
        }}
      >
        <Toolbar sx={{ display: 'flex', justifyContent: 'space-between' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <IconButton
              color="inherit"
              edge="start"
              onClick={() => setMobileOpen(true)}
              sx={{ display: { md: 'none', xs: 'inline-flex' } }}
            >
              <MenuIcon />
            </IconButton>
            <Typography variant="h6" fontWeight={600} sx={{ display: { xs: 'none', md: 'block' } }}>
              {activeLabel}
            </Typography>
            <Typography variant="subtitle1" sx={{ display: { xs: 'block', md: 'none' } }}>
              Simulation Bridge
            </Typography>
          </Box>
          <IconButton color="primary" onClick={() => navigate('/streaming')} size="large">
            <PlayArrowRoundedIcon />
          </IconButton>
        </Toolbar>
      </AppBar>
      <Box component="nav" sx={{ width: { md: drawerWidth }, flexShrink: { md: 0 } }}>
        <Drawer
          variant="temporary"
          open={mobileOpen}
          onClose={() => setMobileOpen(false)}
          ModalProps={{ keepMounted: true }}
          sx={{
            display: { xs: 'block', md: 'none' },
            '& .MuiDrawer-paper': { boxSizing: 'border-box', width: drawerWidth }
          }}
        >
          {drawer}
        </Drawer>
        <Drawer
          variant="permanent"
          sx={{
            display: { xs: 'none', md: 'block' },
            '& .MuiDrawer-paper': { boxSizing: 'border-box', width: drawerWidth }
          }}
          open
        >
          {drawer}
        </Drawer>
      </Box>
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: { xs: 2, md: 4 },
          width: { md: `calc(100% - ${drawerWidth}px)` },
          mt: 8,
          overflow: 'auto'
        }}
      >
        {children}
      </Box>
    </Box>
  );
}

export default Layout;
