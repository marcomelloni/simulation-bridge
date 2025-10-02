import AccessTimeRoundedIcon from '@mui/icons-material/AccessTimeRounded';
import PlayArrowRoundedIcon from '@mui/icons-material/PlayArrowRounded';
import SettingsSuggestRoundedIcon from '@mui/icons-material/SettingsSuggestRounded';
import StopRoundedIcon from '@mui/icons-material/StopRounded';
import {
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Grid,
  Stack,
  TextField,
  ToggleButton,
  ToggleButtonGroup,
  Typography
} from '@mui/material';
import { useState } from 'react';

const schedules = [
  {
    id: 'sch-1',
    name: 'Regression notturna',
    frequency: 'Ogni notte alle 02:00',
    nextRun: 'Prossima esecuzione: domani alle 02:00',
    active: true
  },
  {
    id: 'sch-2',
    name: 'Stress test MQTT',
    frequency: 'Ogni lunedì alle 06:30',
    nextRun: 'Prossima esecuzione: lunedì 06:30',
    active: false
  }
];

function Automations() {
  const [mode, setMode] = useState<'manual' | 'scheduled'>('manual');

  return (
    <Stack spacing={4}>
      <Box>
        <Typography variant="h4" fontWeight={700} gutterBottom>
          Automazioni e Runbook
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Avvia, pianifica e monitora scenari ricorrenti riutilizzando le configurazioni del bridge.
        </Typography>
      </Box>

      <Card>
        <CardContent>
          <Stack direction={{ xs: 'column', md: 'row' }} spacing={3} alignItems={{ md: 'center' }}>
            <Stack spacing={1}>
              <Typography variant="h6" fontWeight={600}>
                Avvia nuova automazione
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Seleziona la configurazione da utilizzare e scegli se eseguire subito o schedulare.
              </Typography>
            </Stack>
            <ToggleButtonGroup
              color="primary"
              exclusive
              value={mode}
              onChange={(_, value) => value && setMode(value)}
            >
              <ToggleButton value="manual">Esecuzione immediata</ToggleButton>
              <ToggleButton value="scheduled">Pianifica esecuzione</ToggleButton>
            </ToggleButtonGroup>
          </Stack>

          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12} md={6}>
              <TextField label="Configurazione" fullWidth placeholder="Seleziona configurazione" />
            </Grid>
            <Grid item xs={12} md={3}>
              <TextField label="Branch" fullWidth placeholder="main" />
            </Grid>
            <Grid item xs={12} md={3}>
              <TextField label="Variabile scenario" fullWidth placeholder="scenario_a" />
            </Grid>
          </Grid>

          {mode === 'scheduled' ? (
            <Grid container spacing={2} sx={{ mt: 1 }}>
              <Grid item xs={12} md={4}>
                <TextField label="Cadenza" fullWidth placeholder="0 2 * * *" />
              </Grid>
              <Grid item xs={12} md={4}>
                <TextField label="Timezone" fullWidth placeholder="Europe/Rome" />
              </Grid>
              <Grid item xs={12} md={4}>
                <TextField label="Durata massima" fullWidth placeholder="120 min" />
              </Grid>
            </Grid>
          ) : (
            <Grid container spacing={2} sx={{ mt: 1 }}>
              <Grid item xs={12} md={6}>
                <TextField label="Timeout" fullWidth placeholder="60 min" />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField label="Ripetizioni" fullWidth placeholder="3" />
              </Grid>
            </Grid>
          )}

          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} sx={{ mt: 3 }}>
            <Button startIcon={<PlayArrowRoundedIcon />} variant="contained" color="primary">
              Avvia automazione
            </Button>
            <Button startIcon={<SettingsSuggestRoundedIcon />} variant="outlined">
              Salva come workflow
            </Button>
          </Stack>
        </CardContent>
      </Card>

      <Card>
        <CardContent>
          <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 2 }}>
            <AccessTimeRoundedIcon color="primary" />
            <Typography variant="h6" fontWeight={600}>
              Pianificazioni attive
            </Typography>
          </Stack>

          <Stack spacing={2}>
            {schedules.map((schedule) => (
              <Card key={schedule.id} variant="outlined">
                <CardContent>
                  <Stack direction={{ xs: 'column', md: 'row' }} justifyContent="space-between" gap={2}>
                    <Box>
                      <Typography variant="subtitle1" fontWeight={600}>
                        {schedule.name}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {schedule.frequency}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {schedule.nextRun}
                      </Typography>
                    </Box>
                    <Stack direction="row" spacing={1} alignItems="center">
                      <Chip
                        label={schedule.active ? 'Attiva' : 'In pausa'}
                        color={schedule.active ? 'success' : 'default'}
                        variant={schedule.active ? 'filled' : 'outlined'}
                      />
                      <Button
                        variant={schedule.active ? 'outlined' : 'contained'}
                        color={schedule.active ? 'inherit' : 'primary'}
                        startIcon={schedule.active ? <StopRoundedIcon /> : <PlayArrowRoundedIcon />}
                      >
                        {schedule.active ? 'Metti in pausa' : 'Riattiva'}
                      </Button>
                    </Stack>
                  </Stack>
                </CardContent>
              </Card>
            ))}
          </Stack>
        </CardContent>
      </Card>
    </Stack>
  );
}

export default Automations;
