import FolderOpenRoundedIcon from '@mui/icons-material/FolderOpenRounded';
import LaunchRoundedIcon from '@mui/icons-material/LaunchRounded';
import MoreVertRoundedIcon from '@mui/icons-material/MoreVertRounded';
import SearchRoundedIcon from '@mui/icons-material/SearchRounded';
import {
  Box,
  Card,
  CardActions,
  CardContent,
  Chip,
  Grid,
  IconButton,
  InputAdornment,
  Stack,
  TextField,
  Typography
} from '@mui/material';

const projects = [
  {
    id: 'proj-1',
    name: 'Linea di produzione 4.0',
    description: 'Scenario ibrido con orchestrazione RabbitMQ e analisi REST.',
    updatedAt: 'Aggiornato 2h fa',
    tags: ['RabbitMQ', 'Analytics']
  },
  {
    id: 'proj-2',
    name: 'Robotica collaborativa',
    description: 'Simulazione streaming in tempo reale per controlli robotici.',
    updatedAt: 'Aggiornato ieri',
    tags: ['Streaming', 'MQTT']
  },
  {
    id: 'proj-3',
    name: 'Fonderia predittiva',
    description: 'Digital twin che sfrutta REST per la telemetria e RabbitMQ per le code.',
    updatedAt: 'Aggiornato 3 giorni fa',
    tags: ['REST', 'RabbitMQ', 'Analytics']
  }
];

function Projects() {
  return (
    <Stack spacing={4}>
      <Box>
        <Typography variant="h4" fontWeight={700} gutterBottom>
          Progetti Simulation Bridge
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Gestisci template, ambienti di test e scenari condivisi con il tuo team.
        </Typography>
      </Box>

      <TextField
        placeholder="Cerca progetti, protocolli o owner"
        fullWidth
        InputProps={{
          startAdornment: (
            <InputAdornment position="start">
              <SearchRoundedIcon color="action" />
            </InputAdornment>
          )
        }}
      />

      <Grid container spacing={3}>
        {projects.map((project) => (
          <Grid item xs={12} md={4} key={project.id}>
            <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
              <CardContent sx={{ flexGrow: 1 }}>
                <Stack direction="row" justifyContent="space-between" alignItems="flex-start">
                  <Stack direction="row" spacing={1} alignItems="center">
                    <FolderOpenRoundedIcon color="primary" />
                    <Typography variant="h6" fontWeight={600}>
                      {project.name}
                    </Typography>
                  </Stack>
                  <IconButton size="small">
                    <MoreVertRoundedIcon fontSize="small" />
                  </IconButton>
                </Stack>
                <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                  {project.description}
                </Typography>
                <Stack direction="row" spacing={1} sx={{ mt: 2, flexWrap: 'wrap' }}>
                  {project.tags.map((tag) => (
                    <Chip key={tag} label={tag} size="small" color="primary" variant="outlined" />
                  ))}
                </Stack>
              </CardContent>
              <CardActions sx={{ justifyContent: 'space-between', px: 3, pb: 3 }}>
                <Typography variant="caption" color="text.secondary">
                  {project.updatedAt}
                </Typography>
                <Chip
                  component="a"
                  href="#"
                  clickable
                  color="primary"
                  icon={<LaunchRoundedIcon />}
                  label="Apri workspace"
                />
              </CardActions>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Stack>
  );
}

export default Projects;
