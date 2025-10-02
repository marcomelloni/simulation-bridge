import AddCommentRoundedIcon from '@mui/icons-material/AddCommentRounded';
import CloudUploadRoundedIcon from '@mui/icons-material/CloudUploadRounded';
import ShareRoundedIcon from '@mui/icons-material/ShareRounded';
import {
  Avatar,
  AvatarGroup,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Divider,
  Grid,
  Stack,
  TextField,
  Typography
} from '@mui/material';

const collaborators = [
  { name: 'Sara', role: 'Digital Twin Engineer', color: '#00bcd4' },
  { name: 'Marco', role: 'Process Owner', color: '#ff9800' },
  { name: 'Anna', role: 'QA Specialist', color: '#8e24aa' }
];

function Collaboration() {
  return (
    <Stack spacing={4}>
      <Box>
        <Typography variant="h4" fontWeight={700} gutterBottom>
          Collaborazione e Condivisione
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Coordina i team multidisciplinari condividendo payload, risultati e note operative.
        </Typography>
      </Box>

      <Grid container spacing={3}>
        <Grid item xs={12} md={7}>
          <Card>
            <CardContent>
              <Stack direction={{ xs: 'column', md: 'row' }} justifyContent="space-between" spacing={3}>
                <Box>
                  <Typography variant="h6" fontWeight={600}>
                    Note condivise per l&apos;esecuzione corrente
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Aggiungi aggiornamenti o richieste per il team prima di avviare una nuova campagna.
                  </Typography>
                </Box>
                <Button variant="contained" startIcon={<AddCommentRoundedIcon />}>
                  Aggiungi nota
                </Button>
              </Stack>

              <Stack spacing={2} sx={{ mt: 3 }}>
                <Box
                  sx={{
                    p: 2,
                    borderRadius: 2,
                    bgcolor: 'grey.50',
                    border: (theme) => `1px solid ${theme.palette.divider}`
                  }}
                >
                  <Typography variant="subtitle2" fontWeight={600}>
                    Aggiornare payload MQTT con i nuovi topic di sicurezza
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Inserita da Sara • 15 minuti fa
                  </Typography>
                </Box>
                <Box
                  sx={{
                    p: 2,
                    borderRadius: 2,
                    bgcolor: 'grey.50',
                    border: (theme) => `1px solid ${theme.palette.divider}`
                  }}
                >
                  <Typography variant="subtitle2" fontWeight={600}>
                    Richiesta report PDF per il comitato di revisione
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Inserita da Anna • 2 ore fa
                  </Typography>
                </Box>
              </Stack>

              <Divider sx={{ my: 3 }} />

              <Stack spacing={2}>
                <Typography variant="subtitle1" fontWeight={600}>
                  Condividi un nuovo allegato
                </Typography>
                <TextField label="Descrizione" fullWidth placeholder="Es. payload di test robotica" />
                <Button variant="outlined" startIcon={<CloudUploadRoundedIcon />}>Carica file</Button>
              </Stack>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={5}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Typography variant="h6" fontWeight={600} gutterBottom>
                Team coinvolti
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Gestisci i permessi di lettura e scrittura sui progetti condivisi.
              </Typography>

              <AvatarGroup max={4} sx={{ mt: 3 }}>
                {collaborators.map((member) => (
                  <Avatar key={member.name} sx={{ bgcolor: member.color }}>
                    {member.name.charAt(0)}
                  </Avatar>
                ))}
              </AvatarGroup>

              <Stack spacing={2} sx={{ mt: 3 }}>
                {collaborators.map((member) => (
                  <Box
                    key={member.name}
                    sx={{
                      p: 2,
                      borderRadius: 2,
                      bgcolor: 'background.default',
                      border: (theme) => `1px solid ${theme.palette.divider}`
                    }}
                  >
                    <Stack direction="row" justifyContent="space-between" alignItems="center">
                      <Box>
                        <Typography variant="subtitle1" fontWeight={600}>
                          {member.name}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {member.role}
                        </Typography>
                      </Box>
                      <Chip icon={<ShareRoundedIcon />} label="Condiviso" color="primary" variant="outlined" />
                    </Stack>
                  </Box>
                ))}
              </Stack>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Stack>
  );
}

export default Collaboration;
