import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import Grid from '@mui/material/Grid';
import Chip from '@mui/material/Chip';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import CardContent from '@mui/material/CardContent';
import CardActions from '@mui/material/CardActions';

import { DashboardContent } from 'src/layouts/dashboard';
import { Iconify } from 'src/components/iconify';

// ----------------------------------------------------------------------

const QUICK_ACTIONS = [
  {
    title: 'הפניית שיחות',
    icon: 'solar:forward-bold-duotone' as const,
    description: 'הגדר הפניית שיחות לשלוחה אחרת',
    color: 'primary',
  },
  {
    title: 'שינוי סיסמת תא קולי',
    icon: 'solar:voicemail-bold-duotone' as const,
    description: 'אפס את סיסמת ה-Voicemail שלך',
    color: 'info',
  },
  {
    title: 'עדכון כתובת MAC',
    icon: 'solar:settings-bold-duotone' as const,
    description: 'עדכן את כתובת ה-MAC של המכשיר',
    color: 'secondary',
  },
  {
    title: 'אתחול מכשיר',
    icon: 'solar:restart-bold' as const,
    description: 'אתחל את מכשיר הטלפון מרחוק',
    color: 'warning',
  },
];

const STATS = [
  { label: 'שיחות היום', value: '12', color: 'primary' },
  { label: 'קריאות פתוחות', value: '2', color: 'warning' },
  { label: 'שיחות שלא נענו', value: '0', color: 'error' },
];

export default function TelephonyDashboardPage() {
  return (
    <DashboardContent maxWidth="xl">
      <Box sx={{ mb: { xs: 3, md: 5 } }}>
        <Typography variant="h4" sx={{ mb: 1 }}>
          פורטל טלפוניה - שירות עצמי
        </Typography>
        <Typography variant="body2" sx={{ color: 'text.secondary' }}>
          ברוך הבא! כאן תוכל לנהל את התחנה הטלפונית שלך ולבצע פעולות שירות עצמי
        </Typography>
      </Box>

      {/* Station Status Card */}
      <Card sx={{ mb: 3, bgcolor: 'primary.lighter' }}>
        <CardContent>
          <Grid container spacing={2} alignItems="center">
            <Grid size={{ xs: 12, md: 6 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <Box
                  sx={{
                    width: 60,
                    height: 60,
                    borderRadius: '50%',
                    bgcolor: 'success.main',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  <Iconify
                    icon="solar:phone-bold-duotone"
                    sx={{ fontSize: 30, color: 'white' }}
                  />
                </Box>
                <Box>
                  <Typography variant="h6">טלפון מחובר</Typography>
                  <Typography variant="body2" color="text.secondary">
                    שלוחה: 1001 | IP: 192.168.1.100
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    מכשיר: Yealink T48U | בסיס: ראשי
                  </Typography>
                </Box>
              </Box>
            </Grid>
            <Grid size={{ xs: 12, md: 6 }}>
              <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', justifyContent: { md: 'flex-end' } }}>
                {STATS.map((stat) => (
                  <Box
                    key={stat.label}
                    sx={{
                      textAlign: 'center',
                      p: 2,
                      borderRadius: 2,
                      bgcolor: 'background.paper',
                    }}
                  >
                    <Typography variant="h4" color={`${stat.color}.main`}>
                      {stat.value}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {stat.label}
                    </Typography>
                  </Box>
                ))}
              </Box>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Quick Actions */}
      <Typography variant="h6" sx={{ mb: 2 }}>
        פעולות מהירות
      </Typography>
      <Grid container spacing={3} sx={{ mb: 4 }}>
        {QUICK_ACTIONS.map((action) => (
          <Grid size={{ xs: 12, sm: 6, md: 3 }} key={action.title}>
            <Card
              sx={{
                height: '100%',
                display: 'flex',
                flexDirection: 'column',
                transition: 'transform 0.2s, box-shadow 0.2s',
                '&:hover': {
                  transform: 'translateY(-4px)',
                  boxShadow: (theme) => theme.shadows[8],
                },
              }}
            >
              <CardContent sx={{ flexGrow: 1, textAlign: 'center' }}>
                <Box
                  sx={{
                    width: 60,
                    height: 60,
                    borderRadius: '50%',
                    bgcolor: `${action.color}.lighter`,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    mx: 'auto',
                    mb: 2,
                  }}
                >
                  <Iconify
                    icon={action.icon}
                    sx={{ fontSize: 30, color: `${action.color}.main` }}
                  />
                </Box>
                <Typography variant="h6" sx={{ mb: 1 }}>
                  {action.title}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {action.description}
                </Typography>
              </CardContent>
              <CardActions sx={{ justifyContent: 'center', pb: 2 }}>
                <Button
                  variant="contained"
                  color={action.color as any}
                  size="small"
                >
                  בצע פעולה
                </Button>
              </CardActions>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Recent Activity */}
      <Grid container spacing={3}>
        <Grid size={{ xs: 12, md: 6 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>
                שיחות אחרונות
              </Typography>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                {[
                  { name: 'ישראל ישראלי', number: '1002', time: '10:23', type: 'incoming' },
                  { name: 'שרה כהן', number: '1005', time: '09:45', type: 'outgoing' },
                  { name: 'דני לוי', number: '1003', time: '09:12', type: 'missed' },
                ].map((call, index) => (
                  <Box
                    key={index}
                    sx={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      p: 1.5,
                      borderRadius: 1,
                      bgcolor: 'background.neutral',
                    }}
                  >
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                      <Iconify
                        icon={
                          call.type === 'incoming'
                            ? 'solar:incoming-call-rounded-bold-duotone'
                            : call.type === 'outgoing'
                            ? 'solar:outgoing-call-rounded-bold-duotone'
                            : 'solar:call-dropped-bold-duotone'
                        }
                        sx={{
                          color:
                            call.type === 'missed'
                              ? 'error.main'
                              : call.type === 'incoming'
                              ? 'success.main'
                              : 'info.main',
                        }}
                      />
                      <Box>
                        <Typography variant="subtitle2">{call.name}</Typography>
                        <Typography variant="caption" color="text.secondary">
                          {call.number}
                        </Typography>
                      </Box>
                    </Box>
                    <Typography variant="caption" color="text.secondary">
                      {call.time}
                    </Typography>
                  </Box>
                ))}
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, md: 6 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>
                התראות אחרונות
              </Typography>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                {[
                  { message: 'סיסמת תא קולי תפוג בעוד 7 ימים', type: 'warning' },
                  { message: 'עדכון מערכת זמין - גרסה 2.5.0', type: 'info' },
                  { message: 'קריאת תמיכה #1234 נסגרה', type: 'success' },
                ].map((alert, index) => (
                  <Box
                    key={index}
                    sx={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 1.5,
                      p: 1.5,
                      borderRadius: 1,
                      bgcolor: 'background.neutral',
                    }}
                  >
                    <Chip
                      size="small"
                      color={alert.type as any}
                      label={
                        alert.type === 'warning'
                          ? 'אזהרה'
                          : alert.type === 'info'
                          ? 'מידע'
                          : 'הצלחה'
                      }
                    />
                    <Typography variant="body2">{alert.message}</Typography>
                  </Box>
                ))}
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </DashboardContent>
  );
}
