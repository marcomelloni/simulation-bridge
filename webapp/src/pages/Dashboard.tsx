import AssessmentRoundedIcon from '@mui/icons-material/AssessmentRounded';
import CloudSyncRoundedIcon from '@mui/icons-material/CloudSyncRounded';
import RocketLaunchRoundedIcon from '@mui/icons-material/RocketLaunchRounded';
import WarningAmberRoundedIcon from '@mui/icons-material/WarningAmberRounded';
import {
  Box,
  Card,
  CardContent,
  Chip,
  Grid,
  LinearProgress,
  Stack,
  Typography
} from '@mui/material';
import { useMemo } from 'react';

const runs = [
  {
    id: 'run-1',
    project: 'Linea di produzione 4.0',
    configuration: 'MQTT + REST orchestration',
    status: 'running',
    progress: 68,
    owner: 'Team Digital Twin'
  },
  {
    id: 'run-2',
    project: 'Robotica collaborativa',
    configuration: 'RabbitMQ real-time streaming',
    status: 'completed',
    progress: 100,
    owner: 'Lab Automazione'
  },
  {
    id: 'run-3',
    project: 'Fonderia predittiva',
    configuration: 'REST analytics',
    status: 'error',
    progress: 5,
    owner: 'Ops Quality'
  }
];

function StatusChip({ status }: { status: string }) {
  const color = useMemo(() => {
    switch (status) {
      case 'running':
        return 'primary';
      case 'completed':
        return 'success';
      case 'error':
        return 'error';
      default:
        return 'default';
    }
  }, [status]);

  const label = useMemo(() => {
    switch (status) {
      case 'running':
        return 'In esecuzione';
      case 'completed':
        return 'Completata';
      case 'error':
        return 'Errore';
      default:
        return status;
    }
  }, [status]);

  return <Chip label={label} color={color as any} size="small" variant="filled" />;
}

function Dashboard() {
  return (
    <Stack spacing={4}>
      <Box>
        <Typography variant="h4" fontWeight={700} gutterBottom>
          Benvenuto nella console Simulation Bridge
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Monitora lo stato dei bridge, visualizza le prestazioni e controlla ogni esecuzione.
        </Typography>
      </Box>

      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Stack direction="row" justifyContent="space-between" alignItems="center">
                <Box>
                  <Typography variant="subtitle2" color="text.secondary">
                    Bridge attivi
                  </Typography>
                  <Typography variant="h3" fontWeight={700}>
                    4
                  </Typography>
                </Box>
                <CloudSyncRoundedIcon color="primary" fontSize="large" />
              </Stack>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                2 orchestrazioni ibride e 2 canali streaming disponibili.
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Stack direction="row" justifyContent="space-between" alignItems="center">
                <Box>
                  <Typography variant="subtitle2" color="text.secondary">
                    Simulazioni oggi
                  </Typography>
                  <Typography variant="h3" fontWeight={700}>
                    18
                  </Typography>
                </Box>
                <RocketLaunchRoundedIcon color="secondary" fontSize="large" />
              </Stack>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                Incluse 5 nuove richieste da team esterni.
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Stack direction="row" justifyContent="space-between" alignItems="center">
                <Box>
                  <Typography variant="subtitle2" color="text.secondary">
                    Incidenti ultimi 7 giorni
                  </Typography>
                  <Typography variant="h3" fontWeight={700}>
                    1
                  </Typography>
                </Box>
                <WarningAmberRoundedIcon color="error" fontSize="large" />
              </Stack>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                Tutte le altre esecuzioni sono state completate con successo.
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Card>
        <CardContent>
          <Stack direction={{ xs: 'column', md: 'row' }} justifyContent="space-between" spacing={3}>
            <Box>
              <Typography variant="h6" fontWeight={600} gutterBottom>
                Esecuzioni correnti
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Controlla l&apos;avanzamento delle simulazioni orchestrate dal bridge.
              </Typography>
            </Box>
            <Chip label="Ultimo aggiornamento: pochi secondi fa" color="default" />
          </Stack>

          <Stack spacing={3} sx={{ mt: 3 }}>
            {runs.map((run) => (
              <Box
                key={run.id}
                sx={{
                  p: 3,
                  borderRadius: 3,
                  bgcolor: 'background.default',
                  border: (theme) => `1px solid ${theme.palette.divider}`
                }}
              >
                <Stack direction={{ xs: 'column', md: 'row' }} justifyContent="space-between" gap={2}>
                  <Box>
                    <Typography variant="subtitle1" fontWeight={600}>
                      {run.project}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {run.configuration}
                    </Typography>
                  </Box>
                  <Stack direction="row" gap={2} alignItems="center">
                    <StatusChip status={run.status} />
                    <Typography variant="body2" color="text.secondary">
                      Referente: {run.owner}
                    </Typography>
                  </Stack>
                </Stack>
                <Box sx={{ mt: 2 }}>
                  <LinearProgress
                    variant="determinate"
                    value={run.progress}
                    sx={{ height: 10, borderRadius: 5 }}
                    color={run.status === 'error' ? 'error' : 'primary'}
                  />
                  <Typography variant="caption" color="text.secondary">
                    Avanzamento {run.progress}%
                  </Typography>
                </Box>
              </Box>
            ))}
          </Stack>
        </CardContent>
      </Card>

      <Card>
        <CardContent>
          <Stack direction={{ xs: 'column', md: 'row' }} justifyContent="space-between" spacing={3}>
            <Stack direction="row" spacing={1} alignItems="center">
              <AssessmentRoundedIcon color="primary" />
              <Box>
                <Typography variant="h6" fontWeight={600}>
                  Metriche recenti
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Latenze e throughput calcolati dalle ultime esecuzioni.
                </Typography>
              </Box>
            </Stack>
            <Chip label="Aggiorna" clickable color="primary" variant="outlined" />
          </Stack>
          <Grid container spacing={3} sx={{ mt: 1 }}>
            <Grid item xs={12} md={4}>
              <Box sx={{ p: 3 }}>
                <Typography variant="subtitle2" color="text.secondary">
                  Latenza media (ms)
                </Typography>
                <Typography variant="h4" fontWeight={700}>
                  184
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={12} md={4}>
              <Box sx={{ p: 3 }}>
                <Typography variant="subtitle2" color="text.secondary">
                  Throughput (req/min)
                </Typography>
                <Typography variant="h4" fontWeight={700}>
                  527
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={12} md={4}>
              <Box sx={{ p: 3 }}>
                <Typography variant="subtitle2" color="text.secondary">
                  Errori ultimi 60 minuti
                </Typography>
                <Typography variant="h4" fontWeight={700}>
                  0
                </Typography>
              </Box>
            </Grid>
          </Grid>
        </CardContent>
      </Card>
    </Stack>
  );
}

export default Dashboard;
