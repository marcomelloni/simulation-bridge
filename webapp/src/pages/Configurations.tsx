import AddRoundedIcon from '@mui/icons-material/AddRounded';
import SaveRoundedIcon from '@mui/icons-material/SaveRounded';
import SettingsEthernetRoundedIcon from '@mui/icons-material/SettingsEthernetRounded';
import {
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Divider,
  FormControl,
  Grid,
  InputLabel,
  MenuItem,
  Select,
  Stack,
  Switch,
  TextField,
  Typography
} from '@mui/material';
import { useState } from 'react';

const defaultConfig = {
  name: 'Bridge principale',
  protocol: 'mqtt',
  tls: true,
  host: 'broker.internal',
  port: 8883,
  username: 'bridge-user',
  password: '••••••••',
  restEndpoint: 'https://bridge.internal/api/v1/execute',
  logLevel: 'INFO'
};

function Configurations() {
  const [config, setConfig] = useState(defaultConfig);

  const handleChange = (field: keyof typeof config, value: string | number | boolean) => {
    setConfig((prev) => ({ ...prev, [field]: value }));
  };

  return (
    <Stack spacing={4}>
      <Box>
        <Typography variant="h4" fontWeight={700} gutterBottom>
          Configurazioni del Bridge
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Modifica i parametri dei protocolli, esporta i profili e applica le configurazioni ai nodi.
        </Typography>
      </Box>

      <Grid container spacing={3}>
        <Grid item xs={12} md={7}>
          <Card>
            <CardContent>
              <Stack direction="row" justifyContent="space-between" alignItems="center">
                <Stack direction="row" spacing={1} alignItems="center">
                  <SettingsEthernetRoundedIcon color="primary" />
                  <Typography variant="h6" fontWeight={600}>
                    Parametri principali
                  </Typography>
                </Stack>
                <Chip label="MQTT attivo" color="primary" />
              </Stack>

              <Grid container spacing={2} sx={{ mt: 1 }}>
                <Grid item xs={12} md={6}>
                  <TextField
                    label="Nome"
                    fullWidth
                    value={config.name}
                    onChange={(event) => handleChange('name', event.target.value)}
                  />
                </Grid>
                <Grid item xs={12} md={6}>
                  <FormControl fullWidth>
                    <InputLabel id="protocol-label">Protocollo</InputLabel>
                    <Select
                      labelId="protocol-label"
                      label="Protocollo"
                      value={config.protocol}
                      onChange={(event) => handleChange('protocol', event.target.value)}
                    >
                      <MenuItem value="mqtt">MQTT</MenuItem>
                      <MenuItem value="rabbitmq">RabbitMQ</MenuItem>
                      <MenuItem value="rest">REST</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={12} md={6}>
                  <TextField
                    label="Host"
                    fullWidth
                    value={config.host}
                    onChange={(event) => handleChange('host', event.target.value)}
                  />
                </Grid>
                <Grid item xs={12} md={3}>
                  <TextField
                    label="Porta"
                    fullWidth
                    type="number"
                    value={config.port}
                    onChange={(event) => handleChange('port', Number(event.target.value))}
                  />
                </Grid>
                <Grid item xs={12} md={3}>
                  <Stack direction="row" spacing={1} alignItems="center" sx={{ height: '100%' }}>
                    <Typography variant="subtitle2">TLS</Typography>
                    <Switch
                      checked={config.tls}
                      onChange={(event) => handleChange('tls', event.target.checked)}
                    />
                  </Stack>
                </Grid>
                <Grid item xs={12} md={6}>
                  <TextField
                    label="Username"
                    fullWidth
                    value={config.username}
                    onChange={(event) => handleChange('username', event.target.value)}
                  />
                </Grid>
                <Grid item xs={12} md={6}>
                  <TextField
                    label="Password"
                    type="password"
                    fullWidth
                    value={config.password}
                    onChange={(event) => handleChange('password', event.target.value)}
                  />
                </Grid>
                <Grid item xs={12}>
                  <TextField
                    label="Endpoint REST di fallback"
                    fullWidth
                    value={config.restEndpoint}
                    onChange={(event) => handleChange('restEndpoint', event.target.value)}
                  />
                </Grid>
                <Grid item xs={12} md={6}>
                  <FormControl fullWidth>
                    <InputLabel id="log-label">Log level</InputLabel>
                    <Select
                      labelId="log-label"
                      label="Log level"
                      value={config.logLevel}
                      onChange={(event) => handleChange('logLevel', event.target.value)}
                    >
                      <MenuItem value="DEBUG">DEBUG</MenuItem>
                      <MenuItem value="INFO">INFO</MenuItem>
                      <MenuItem value="WARNING">WARNING</MenuItem>
                      <MenuItem value="ERROR">ERROR</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
              </Grid>

              <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} sx={{ mt: 3 }}>
                <Button variant="contained" color="primary" startIcon={<SaveRoundedIcon />}>
                  Salva configurazione
                </Button>
                <Button variant="outlined" startIcon={<AddRoundedIcon />}>
                  Duplica profilo
                </Button>
              </Stack>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={5}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Typography variant="h6" fontWeight={600} gutterBottom>
                Snippet YAML generato
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Copia il contenuto per aggiornarlo nei deployment esistenti o salvarlo come template.
              </Typography>
              <Box
                component="pre"
                sx={{
                  mt: 2,
                  bgcolor: 'grey.100',
                  p: 2,
                  borderRadius: 2,
                  fontSize: 13,
                  overflowX: 'auto'
                }}
              >
{`bridge:\n  name: ${config.name}\n  protocol: ${config.protocol}\n  tls: ${config.tls}\n  host: ${config.host}\n  port: ${config.port}\n  credentials:\n    username: ${config.username}\n    password: ${config.password}\n  restFallback: ${config.restEndpoint}\nlogging:\n  level: ${config.logLevel}`}
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Card>
        <CardContent>
          <Typography variant="h6" fontWeight={600} gutterBottom>
            Adapter abilitati
          </Typography>
          <Divider sx={{ my: 2 }} />
          <Grid container spacing={2}>
            {[{ label: 'MQTT broker', enabled: true }, { label: 'RabbitMQ', enabled: false }, { label: 'REST orchestrator', enabled: true }].map(
              (adapter) => (
                <Grid item xs={12} md={4} key={adapter.label}>
                  <Card variant="outlined">
                    <CardContent>
                      <Stack direction="row" justifyContent="space-between" alignItems="center">
                        <Typography variant="subtitle1" fontWeight={600}>
                          {adapter.label}
                        </Typography>
                        <Switch defaultChecked={adapter.enabled} />
                      </Stack>
                      <Typography variant="body2" color="text.secondary">
                        {adapter.enabled
                          ? 'Attivo e pronto a ricevere richieste.'
                          : 'Disabilitato, abilitalo per utilizzarlo nelle simulazioni.'}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
              )
            )}
          </Grid>
        </CardContent>
      </Card>
    </Stack>
  );
}

export default Configurations;
