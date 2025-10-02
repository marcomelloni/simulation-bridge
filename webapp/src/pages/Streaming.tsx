import CastRoundedIcon from '@mui/icons-material/CastRounded';
import RefreshRoundedIcon from '@mui/icons-material/RefreshRounded';
import SensorsRoundedIcon from '@mui/icons-material/SensorsRounded';
import WarningRoundedIcon from '@mui/icons-material/WarningRounded';
import {
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Divider,
  Grid,
  LinearProgress,
  Stack,
  Switch,
  Typography
} from '@mui/material';

const streams = [
  {
    id: 'stream-1',
    name: 'Linea 4.0 Robotica',
    protocol: 'MQTT',
    rate: '120 msg/min',
    health: 'Buono',
    latency: 210,
    active: true
  },
  {
    id: 'stream-2',
    name: 'Magazzino automatico',
    protocol: 'RabbitMQ',
    rate: '95 msg/min',
    health: 'Attenzione',
    latency: 310,
    active: true
  },
  {
    id: 'stream-3',
    name: 'Controllo qualità',
    protocol: 'REST streaming',
    rate: '45 msg/min',
    health: 'Offline',
    latency: 0,
    active: false
  }
];

function Streaming() {
  return (
    <Stack spacing={4}>
      <Box>
        <Typography variant="h4" fontWeight={700} gutterBottom>
          Streaming e Telemetria
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Monitora i canali di streaming gestiti dal bridge e agisci in tempo reale.
        </Typography>
      </Box>

      <Card>
        <CardContent>
          <Stack direction={{ xs: 'column', md: 'row' }} justifyContent="space-between" alignItems={{ md: 'center' }}>
            <Stack direction="row" spacing={1} alignItems="center">
              <SensorsRoundedIcon color="primary" />
              <Box>
                <Typography variant="h6" fontWeight={600}>
                  Stato generatore streaming
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Abilita o disabilita l&apos;invio di aggiornamenti live ai client connessi.
                </Typography>
              </Box>
            </Stack>
            <Stack direction="row" spacing={2} alignItems="center">
              <Typography variant="subtitle2">Streaming globale</Typography>
              <Switch defaultChecked />
              <Button startIcon={<RefreshRoundedIcon />} variant="outlined">
                Resetta connessioni
              </Button>
            </Stack>
          </Stack>
        </CardContent>
      </Card>

      <Grid container spacing={3}>
        {streams.map((stream) => (
          <Grid item xs={12} md={4} key={stream.id}>
            <Card>
              <CardContent>
                <Stack direction="row" justifyContent="space-between" alignItems="flex-start">
                  <Stack>
                    <Typography variant="h6" fontWeight={600}>
                      {stream.name}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {stream.protocol}
                    </Typography>
                  </Stack>
                  <Chip
                    label={stream.health}
                    color={stream.health === 'Buono' ? 'success' : stream.health === 'Offline' ? 'default' : 'warning'}
                    icon={stream.health === 'Attenzione' ? <WarningRoundedIcon /> : undefined}
                  />
                </Stack>
                <Divider sx={{ my: 2 }} />
                <Typography variant="subtitle2" color="text.secondary">
                  Frequenza
                </Typography>
                <Typography variant="body1" fontWeight={600}>
                  {stream.rate}
                </Typography>
                <Typography variant="subtitle2" color="text.secondary" sx={{ mt: 2 }}>
                  Latenza media
                </Typography>
                <LinearProgress
                  variant="determinate"
                  value={Math.min(stream.latency / 4, 100)}
                  color={stream.latency > 280 ? 'error' : stream.latency > 220 ? 'warning' : 'primary'}
                  sx={{ height: 10, borderRadius: 5 }}
                />
                <Typography variant="caption" color="text.secondary">
                  {stream.latency ? `${stream.latency} ms` : 'Offline'}
                </Typography>
                <Stack direction="row" spacing={1} sx={{ mt: 2 }}>
                  <Chip label={stream.active ? 'Attivo' : 'Disabilitato'} color={stream.active ? 'primary' : 'default'} />
                  <Button size="small" variant="text" endIcon={<CastRoundedIcon />}>
                    Connetti viewer
                  </Button>
                </Stack>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Stack>
  );
}

export default Streaming;
