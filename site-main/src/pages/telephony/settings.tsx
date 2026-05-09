import { useState } from 'react';

import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import Grid from '@mui/material/Grid';
import Switch from '@mui/material/Switch';
import Button from '@mui/material/Button';
import Select from '@mui/material/Select';
import Divider from '@mui/material/Divider';
import MenuItem from '@mui/material/MenuItem';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';
import CardHeader from '@mui/material/CardHeader';
import CardContent from '@mui/material/CardContent';
import FormControl from '@mui/material/FormControl';
import InputLabel from '@mui/material/InputLabel';
import FormControlLabel from '@mui/material/FormControlLabel';

import { DashboardContent } from 'src/layouts/dashboard';
import { Iconify } from 'src/components/iconify';

// ----------------------------------------------------------------------

export default function SettingsPage() {
  const [forwardEnabled, setForwardEnabled] = useState(false);
  const [dndEnabled, setDndEnabled] = useState(false);
  const [voicemailEnabled, setVoicemailEnabled] = useState(true);

  return (
    <DashboardContent maxWidth="lg">
      <Typography variant="h4" sx={{ mb: 3 }}>
        הגדרות מערכת
      </Typography>

      {/* Call Forwarding */}
      <Card sx={{ mb: 3 }}>
        <CardHeader
          title="הפניית שיחות"
          subheader="הגדר מForwarding לשלוחה אחרת כאשר אתה לא זמין"
          avatar={<Iconify icon="solar:forward-bold-duotone" sx={{ fontSize: 32, color: 'primary.main' }} />}
        />
        <CardContent>
          <FormControlLabel
            control={
              <Switch
                checked={forwardEnabled}
                onChange={(e) => setForwardEnabled(e.target.checked)}
              />
            }
            label="הפעל הפניית שיחות"
          />
          {forwardEnabled && (
            <Box sx={{ mt: 2 }}>
              <Grid container spacing={2}>
                <Grid size={{ xs: 12, md: 6 }}>
                  <FormControl fullWidth>
                    <InputLabel>סוג הפניה</InputLabel>
                    <Select label="סוג הפניה" defaultValue="always">
                      <MenuItem value="always">תמיד</MenuItem>
                      <MenuItem value="busy">כשתפוס</MenuItem>
                      <MenuItem value="no_answer">כשלא עונה</MenuItem>
                      <MenuItem value="unavailable">כשלא זמין</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
                <Grid size={{ xs: 12, md: 6 }}>
                  <TextField label="שלוחת יעד" fullWidth placeholder="למשל: 1002" />
                </Grid>
              </Grid>
            </Box>
          )}
        </CardContent>
      </Card>

      {/* Do Not Disturb */}
      <Card sx={{ mb: 3 }}>
        <CardHeader
          title="Do Not Disturb (DND)"
          subheader="חסום את כל השיחות הנכנסות"
          avatar={<Iconify icon="solar:call-dropped-bold-duotone" sx={{ fontSize: 32, color: 'error.main' }} />}
        />
        <CardContent>
          <FormControlLabel
            control={
              <Switch
                checked={dndEnabled}
                onChange={(e) => setDndEnabled(e.target.checked)}
              />
            }
            label="הפעל DND"
          />
          {dndEnabled && (
            <Box sx={{ mt: 2, p: 2, bgcolor: 'error.lighter', borderRadius: 1 }}>
              <Typography variant="body2" color="error.dark">
                <Iconify icon="solar:shield-keyhole-bold-duotone" sx={{ mr: 1, verticalAlign: 'middle' }} />
                כל השיחות הנכנסות יועברו ישירות לתא הקולי
              </Typography>
            </Box>
          )}
        </CardContent>
      </Card>

      {/* Voicemail Settings */}
      <Card sx={{ mb: 3 }}>
        <CardHeader
          title="תא קולי"
          subheader="הגדר את תא הקולי שלך"
          avatar={<Iconify icon="solar:voicemail-bold-duotone" sx={{ fontSize: 32, color: 'info.main' }} />}
        />
        <CardContent>
          <FormControlLabel
            control={
              <Switch
                checked={voicemailEnabled}
                onChange={(e) => setVoicemailEnabled(e.target.checked)}
              />
            }
            label="הפעל תא קולי"
          />
          <Divider sx={{ my: 2 }} />
          <Grid container spacing={2}>
            <Grid size={{ xs: 12, md: 6 }}>
              <TextField label="סיסמת תא קולי" type="password" fullWidth />
            </Grid>
            <Grid size={{ xs: 12, md: 6 }}>
              <TextField label="אימות סיסמה" type="password" fullWidth />
            </Grid>
            <Grid size={{ xs: 12 }}>
              <TextField label="הודעת ברוכים הבאים" multiline rows={3} fullWidth />
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Caller ID */}
      <Card sx={{ mb: 3 }}>
        <CardHeader
          title="Caller ID"
          subheader="הגדר את מספר המזהה שיוצג בשיחות יוצאות"
          avatar={<Iconify icon="solar:user-id-bold-duotone" sx={{ fontSize: 32, color: 'success.main' }} />}
        />
        <CardContent>
          <Grid container spacing={2}>
            <Grid size={{ xs: 12, md: 6 }}>
              <FormControl fullWidth>
                <InputLabel>מספר מזהה</InputLabel>
                <Select label="מספר מזהה" defaultValue="extension">
                  <MenuItem value="extension">שלוחה פנימית (1001)</MenuItem>
                  <MenuItem value="main">מספר ראשי (02-5550000)</MenuItem>
                  <MenuItem value="private">חסוי</MenuItem>
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Device Settings */}
      <Card sx={{ mb: 3 }}>
        <CardHeader
          title="מכשיר טלפון"
          subheader="הגדרות מכשיר הטלפון שלך"
          avatar={<Iconify icon="solar:settings-bold-duotone" sx={{ fontSize: 32, color: 'secondary.main' }} />}
        />
        <CardContent>
          <Grid container spacing={2}>
            <Grid size={{ xs: 12, md: 6 }}>
              <TextField label="כתובת MAC" fullWidth defaultValue="00:1A:2B:3C:4D:5E" />
            </Grid>
            <Grid size={{ xs: 12, md: 6 }}>
              <FormControl fullWidth>
                <InputLabel>רינגטון</InputLabel>
                <Select label="רינגטון" defaultValue="classic">
                  <MenuItem value="classic">קלאסי</MenuItem>
                  <MenuItem value="modern">מודרני</MenuItem>
                  <MenuItem value="soft">עדין</MenuItem>
                  <MenuItem value="business">עסקי</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid size={{ xs: 12 }}>
              <FormControlLabel
                control={<Switch defaultChecked />}
                label="הפעל חייגן מהיר"
              />
            </Grid>
          </Grid>
          <Box sx={{ mt: 2 }}>
            <Button variant="outlined" color="warning" startIcon={<Iconify icon="solar:restart-bold" />}>
              אתחל מכשיר מרחוק
            </Button>
          </Box>
        </CardContent>
      </Card>

      {/* Save Button */}
      <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 2 }}>
        <Button variant="outlined">ביטול</Button>
        <Button variant="contained" startIcon={<Iconify icon="solar:check-circle-bold" />}>
          שמור הגדרות
        </Button>
      </Box>
    </DashboardContent>
  );
}
