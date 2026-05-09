import { useState } from 'react';

import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import Grid from '@mui/material/Grid';
import Chip from '@mui/material/Chip';
import Button from '@mui/material/Button';
import Avatar from '@mui/material/Avatar';
import Typography from '@mui/material/Typography';
import CardContent from '@mui/material/CardContent';
import CardHeader from '@mui/material/CardHeader';
import TextField from '@mui/material/TextField';
import Tab from '@mui/material/Tab';
import Tabs from '@mui/material/Tabs';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemText from '@mui/material/ListItemText';
import ListItemIcon from '@mui/material/ListItemIcon';
import Divider from '@mui/material/Divider';
import Switch from '@mui/material/Switch';
import FormControlLabel from '@mui/material/FormControlLabel';

import { DashboardContent } from 'src/layouts/dashboard';
import { Iconify } from 'src/components/iconify';

// ----------------------------------------------------------------------

const ACTIVITY_LOG = [
  { action: 'התחבר למערכת', time: '10:23', date: '2024-01-15', type: 'login' },
  { action: 'שינה סיסמת תא קולי', time: '09:45', date: '2024-01-15', type: 'settings' },
  { action: 'פתח קריאת תמיכה #1234', time: '14:20', date: '2024-01-14', type: 'ticket' },
  { action: 'עדכן כתובת MAC', time: '11:30', date: '2024-01-14', type: 'settings' },
  { action: 'התחבר למערכת', time: '08:15', date: '2024-01-14', type: 'login' },
];

const PERMISSIONS = [
  { name: 'ניהול שיחות', granted: true, description: 'יכולת להפנות ולנהל שיחות' },
  { name: 'עדכון הגדרות', granted: true, description: 'שינוי הגדרות אישיות' },
  { name: 'צפייה בהקלטות', granted: false, description: 'גישה להקלטות שיחות' },
  { name: 'ניהול משתמשים', granted: false, description: 'הוספה ועריכת משתמשים' },
  { name: 'דוחות מתקדמים', granted: true, description: 'צפייה בדוחות מערכת' },
  { name: 'תמיכה טכנית', granted: true, description: 'פתיחת קריאות תמיכה' },
];

export default function ProfilePage() {
  const [tabValue, setTabValue] = useState(0);
  const [permissions, setPermissions] = useState(PERMISSIONS);

  const handlePermissionChange = (index: number) => {
    const newPermissions = [...permissions];
    newPermissions[index].granted = !newPermissions[index].granted;
    setPermissions(newPermissions);
  };

  return (
    <DashboardContent maxWidth="lg">
      <Typography variant="h4" sx={{ mb: 3 }}>
        פרופיל משתמש
      </Typography>

      <Grid container spacing={3}>
        {/* Profile Card */}
        <Grid size={{ xs: 12, md: 4 }}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Avatar
                sx={{
                  width: 120,
                  height: 120,
                  mx: 'auto',
                  mb: 2,
                  bgcolor: 'primary.main',
                  fontSize: 48,
                }}
              >
                דל
              </Avatar>
              <Typography variant="h5">דני לוי</Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                מחלקת IT | שלוחה 1001
              </Typography>
              <Chip label="מנהל מערכת" color="primary" size="small" sx={{ mb: 2 }} />
              
              <Box sx={{ display: 'flex', justifyContent: 'center', gap: 1, mb: 2 }}>
                <Chip 
                  icon={<Iconify icon="solar:phone-bold-duotone" />} 
                  label="02-5551001" 
                  variant="outlined" 
                  size="small"
                />
              </Box>

              <Button variant="contained" fullWidth sx={{ mb: 1 }}>
                עריכת פרופיל
              </Button>
              <Button variant="outlined" color="error" fullWidth>
                התנתק
              </Button>
            </CardContent>
          </Card>

          {/* Contact Info */}
          <Card sx={{ mt: 2 }}>
            <CardHeader title="פרטי התקשרות" />
            <CardContent>
              <List dense>
                <ListItem>
                  <ListItemIcon>
                    <Iconify icon="solar:letter-bold-duotone" color="primary" />
                  </ListItemIcon>
                  <ListItemText primary="dani.levi@iaf.gov.il" secondary="אימייל" />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <Iconify icon="solar:phone-bold-duotone" color="primary" />
                  </ListItemIcon>
                  <ListItemText primary="02-5551001" secondary="טלפון פנימי" />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <Iconify icon="solar:smartphone-bold-duotone" color="primary" />
                  </ListItemIcon>
                  <ListItemText primary="054-1234567" secondary="טלפון נייד" />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <Iconify icon="solar:map-point-bold-duotone" color="primary" />
                  </ListItemIcon>
                  <ListItemText primary="בניין 5, קומה 3, חדר 302" secondary="מיקום" />
                </ListItem>
              </List>
            </CardContent>
          </Card>
        </Grid>

        {/* Main Content */}
        <Grid size={{ xs: 12, md: 8 }}>
          <Card>
            <Tabs
              value={tabValue}
              onChange={(e, newValue) => setTabValue(newValue)}
              sx={{ borderBottom: 1, borderColor: 'divider' }}
            >
              <Tab label="פרטים אישיים" />
              <Tab label="הרשאות" />
              <Tab label="יומן פעילות" />
              <Tab label="אבטחה" />
            </Tabs>

            <CardContent>
              {tabValue === 0 && (
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                  <Grid container spacing={2}>
                    <Grid size={{ xs: 12, sm: 6 }}>
                      <TextField fullWidth label="שם פרטי" defaultValue="דני" />
                    </Grid>
                    <Grid size={{ xs: 12, sm: 6 }}>
                      <TextField fullWidth label="שם משפחה" defaultValue="לוי" />
                    </Grid>
                    <Grid size={{ xs: 12, sm: 6 }}>
                      <TextField fullWidth label="תעודת זהות" defaultValue="123456789" />
                    </Grid>
                    <Grid size={{ xs: 12, sm: 6 }}>
                      <TextField fullWidth label="דרגה" defaultValue="סא" />
                    </Grid>
                    <Grid size={{ xs: 12, sm: 6 }}>
                      <TextField fullWidth label="מחלקה" defaultValue="מחלקת IT" />
                    </Grid>
                    <Grid size={{ xs: 12, sm: 6 }}>
                      <TextField fullWidth label="תפקיד" defaultValue="מנהל מערכות" />
                    </Grid>
                    <Grid size={{ xs: 12 }}>
                      <TextField fullWidth label="שלוחה" defaultValue="1001" />
                    </Grid>
                    <Grid size={{ xs: 12 }}>
                      <TextField fullWidth multiline rows={3} label="תיאור תפקיד" defaultValue="אחראי על תחזוקת מערכות הטלפוניה והתקשורת" />
                    </Grid>
                  </Grid>
                  <Box sx={{ display: 'flex', gap: 1, justifyContent: 'flex-end' }}>
                    <Button variant="outlined">ביטול</Button>
                    <Button variant="contained">שמור שינויים</Button>
                  </Box>
                </Box>
              )}

              {tabValue === 1 && (
                <Box>
                  <Typography variant="h6" sx={{ mb: 2 }}>הרשאות במערכת</Typography>
                  <List>
                    {permissions.map((perm, index) => (
                      <ListItem key={perm.name}>
                        <ListItemText 
                          primary={perm.name} 
                          secondary={perm.description}
                        />
                        <FormControlLabel
                          control={
                            <Switch
                              checked={perm.granted}
                              onChange={() => handlePermissionChange(index)}
                              color={perm.granted ? 'success' : 'default'}
                            />
                          }
                          label={perm.granted ? 'מאושר' : 'חסום'}
                        />
                      </ListItem>
                    ))}
                  </List>
                </Box>
              )}

              {tabValue === 2 && (
                <Box>
                  <Typography variant="h6" sx={{ mb: 2 }}>יומן פעילות אחרונה</Typography>
                  <List>
                    {ACTIVITY_LOG.map((activity, index) => (
                      <ListItem key={index}>
                        <ListItemIcon>
                          <Iconify 
                            icon={
                              activity.type === 'login' ? 'solar:login-3-bold-duotone' :
                              activity.type === 'settings' ? 'solar:settings-bold-duotone' :
                              'solar:ticket-bold-duotone'
                            }
                            color="primary"
                          />
                        </ListItemIcon>
                        <ListItemText 
                          primary={activity.action} 
                          secondary={`${activity.date} | ${activity.time}`}
                        />
                      </ListItem>
                    ))}
                  </List>
                </Box>
              )}

              {tabValue === 3 && (
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography variant="h6" sx={{ mb: 2 }}>שינוי סיסמה</Typography>
                      <Grid container spacing={2}>
                        <Grid size={{ xs: 12 }}>
                          <TextField fullWidth type="password" label="סיסמה נוכחית" />
                        </Grid>
                        <Grid size={{ xs: 12 }}>
                          <TextField fullWidth type="password" label="סיסמה חדשה" />
                        </Grid>
                        <Grid size={{ xs: 12 }}>
                          <TextField fullWidth type="password" label="אימות סיסמה חדשה" />
                        </Grid>
                      </Grid>
                      <Button variant="contained" sx={{ mt: 2 }}>עדכן סיסמה</Button>
                    </CardContent>
                  </Card>

                  <Card variant="outlined">
                    <CardContent>
                      <Typography variant="h6" sx={{ mb: 2 }}>אימות דו-שלבי (2FA)</Typography>
                      <FormControlLabel
                        control={<Switch defaultChecked />}
                        label="הפעל אימות דו-שלבי"
                      />
                      <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                        ישלח קוד אימות לטלפון הנייד שלך בכל התחברות
                      </Typography>
                    </CardContent>
                  </Card>

                  <Card variant="outlined">
                    <CardContent>
                      <Typography variant="h6" sx={{ mb: 2, color: 'error.main' }}>אזור מסוכן</Typography>
                      <Button variant="outlined" color="error" startIcon={<Iconify icon="solar:trash-bin-trash-bold-duotone" />}>
                        מחק חשבון
                      </Button>
                    </CardContent>
                  </Card>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </DashboardContent>
  );
}
