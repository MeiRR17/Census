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
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemText from '@mui/material/ListItemText';
import ListItemAvatar from '@mui/material/ListItemAvatar';
import IconButton from '@mui/material/IconButton';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import FormControl from '@mui/material/FormControl';
import InputLabel from '@mui/material/InputLabel';
import Select from '@mui/material/Select';
import MenuItem from '@mui/material/MenuItem';

import { DashboardContent } from 'src/layouts/dashboard';
import { Iconify } from 'src/components/iconify';

// ----------------------------------------------------------------------

const CONFERENCE_ROOMS = [
  { id: 'CONF-001', name: 'חדר ועדה ראשי', number: '5001', participants: 8, maxParticipants: 20, status: 'active', organizer: 'דני לוי' },
  { id: 'CONF-002', name: 'צוות IT', number: '5002', participants: 5, maxParticipants: 10, status: 'idle', organizer: 'שרה כהן' },
  { id: 'CONF-003', name: 'מחלקת מבצעים', number: '5003', participants: 12, maxParticipants: 30, status: 'active', organizer: 'משה רבינו' },
  { id: 'CONF-004', name: 'ישיבות חירום', number: '5004', participants: 0, maxParticipants: 50, status: 'idle', organizer: null },
];

const ACTIVE_PARTICIPANTS = [
  { name: 'דני לוי', extension: '1001', role: 'מארח', isMuted: false, isSpeaking: true },
  { name: 'שרה כהן', extension: '1002', role: 'משתתף', isMuted: true, isSpeaking: false },
  { name: 'משה רבינו', extension: '1003', role: 'משתתף', isMuted: false, isSpeaking: false },
  { name: 'רחל גרין', extension: '1004', role: 'משתתף', isMuted: false, isSpeaking: true },
  { name: 'אבי כהן', extension: '1005', role: 'משתתף', isMuted: true, isSpeaking: false },
];

const UPCOMING_MEETINGS = [
  { id: 1, title: 'ישיבת צוות שבועית', room: '5001', time: '10:00', date: '2024-01-16', participants: 8 },
  { id: 2, title: 'תדרוך מבצעי', room: '5003', time: '14:00', date: '2024-01-16', participants: 15 },
  { id: 3, title: 'סקום חירום', room: '5004', time: '16:30', date: '2024-01-16', participants: 25 },
];

export default function ConferencePage() {
  const [openCreateDialog, setOpenCreateDialog] = useState(false);
  const [selectedRoom, setSelectedRoom] = useState<string | null>(null);

  return (
    <DashboardContent maxWidth="xl">
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">שיחות ועידה</Typography>
        <Button
          variant="contained"
          startIcon={<Iconify icon="mingcute:add-line" />}
          onClick={() => setOpenCreateDialog(true)}
        >
          צור חדר חדש
        </Button>
      </Box>

      <Grid container spacing={3}>
        {/* Active Conference */}
        <Grid size={{ xs: 12, md: 8 }}>
          <Card>
            <CardHeader
              title="חדר ועידה פעיל"
              subheader="חדר 5001 - ישיבת צוות שבועית"
              action={
                <Box sx={{ display: 'flex', gap: 1 }}>
                  <Chip label="8 משתתפים" color="success" />
                  <Button variant="outlined" color="error" size="small">
                    סיים שיחה
                  </Button>
                </Box>
              }
            />
            <CardContent>
              {/* Controls */}
              <Box sx={{ display: 'flex', justifyContent: 'center', gap: 2, mb: 3 }}>
                <Button variant="contained" color={true ? 'error' : 'primary'} startIcon={<Iconify icon="solar:microphone-bold-duotone" />}>
                  השתק
                </Button>
                <Button variant="contained" color="primary" startIcon={<Iconify icon="solar:phone-bold-duotone" />}>
                  חייג משתתף
                </Button>
                <Button variant="contained" color="secondary" startIcon={<Iconify icon="solar:record-bold-duotone" />}>
                  הקלט
                </Button>
                <Button variant="outlined" startIcon={<Iconify icon="solar:share-bold-duotone" />}>
                  שתף מסך
                </Button>
              </Box>

              <Typography variant="h6" sx={{ mb: 2 }}>משתתפים פעילים</Typography>
              <List>
                {ACTIVE_PARTICIPANTS.map((participant, index) => (
                  <ListItem
                    key={index}
                    secondaryAction={
                      <Box sx={{ display: 'flex', gap: 1 }}>
                        <IconButton size="small" color={participant.isMuted ? 'error' : 'default'}>
                          <Iconify icon={participant.isMuted ? 'solar:microphone-off-bold' : 'solar:microphone-bold'} />
                        </IconButton>
                        <IconButton size="small" color="error">
                          <Iconify icon="solar:phone-missed-bold" />
                        </IconButton>
                      </Box>
                    }
                  >
                    <ListItemAvatar>
                      <Avatar sx={{ bgcolor: participant.isSpeaking ? 'success.main' : 'grey.400' }}>
                        {participant.name.charAt(0)}
                      </Avatar>
                    </ListItemAvatar>
                    <ListItemText
                      primary={participant.name}
                      secondary={`שלוחה ${participant.extension} | ${participant.role}`}
                    />
                    {participant.isSpeaking && (
                      <Chip size="small" color="success" label="מדבר" sx={{ mr: 8 }} />
                    )}
                  </ListItem>
                ))}
              </List>
            </CardContent>
          </Card>

          {/* Conference Rooms */}
          <Card sx={{ mt: 3 }}>
            <CardHeader title="חדרי ועידה זמינים" />
            <CardContent>
              <Grid container spacing={2}>
                {CONFERENCE_ROOMS.map((room) => (
                  <Grid size={{ xs: 12, sm: 6 }} key={room.id}>
                    <Card variant="outlined" sx={{ cursor: 'pointer', '&:hover': { borderColor: 'primary.main' } }}>
                      <CardContent>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                          <Box>
                            <Typography variant="h6">{room.name}</Typography>
                            <Typography variant="body2" color="text.secondary">
                              מספר: {room.number}
                            </Typography>
                          </Box>
                          <Chip
                            size="small"
                            color={room.status === 'active' ? 'success' : 'default'}
                            label={room.status === 'active' ? 'פעיל' : 'פנוי'}
                          />
                        </Box>
                        <Box sx={{ mt: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Iconify icon="solar:users-group-rounded-bold-duotone" color="primary" />
                          <Typography variant="body2">
                            {room.participants} / {room.maxParticipants} משתתפים
                          </Typography>
                        </Box>
                        {room.organizer && (
                          <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                            מארח: {room.organizer}
                          </Typography>
                        )}
                        <Button variant="outlined" fullWidth sx={{ mt: 2 }}>
                          {room.status === 'active' ? 'הצטרף' : 'התחל שיחה'}
                        </Button>
                      </CardContent>
                    </Card>
                  </Grid>
                ))}
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* Sidebar */}
        <Grid size={{ xs: 12, md: 4 }}>
          {/* Quick Join */}
          <Card sx={{ mb: 3 }}>
            <CardHeader title="הצטרף מהר" />
            <CardContent>
              <TextField
                fullWidth
                label="מספר חדר"
                placeholder="הזן מספר חדר (למשל: 5001)"
                sx={{ mb: 2 }}
              />
              <Button variant="contained" fullWidth startIcon={<Iconify icon="solar:phone-bold-duotone" />}>
                התקשר
              </Button>
            </CardContent>
          </Card>

          {/* Upcoming Meetings */}
          <Card>
            <CardHeader title="ישיבות מתוכננות" />
            <CardContent>
              <List dense>
                {UPCOMING_MEETINGS.map((meeting) => (
                  <ListItem key={meeting.id}>
                    <ListItemText
                      primary={meeting.title}
                      secondary={`${meeting.date} | ${meeting.time} | חדר ${meeting.room}`}
                    />
                    <Chip size="small" label={`${meeting.participants} משתתפים`} />
                  </ListItem>
                ))}
              </List>
              <Button variant="outlined" fullWidth sx={{ mt: 2 }}>
                צור פגישה חדשה
              </Button>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Create Room Dialog */}
      <Dialog open={openCreateDialog} onClose={() => setOpenCreateDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>צור חדר ועידה חדש</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1 }}>
            <TextField label="שם החדר" fullWidth />
            <TextField label="מספר חדר" fullWidth placeholder="למשל: 5005" />
            <FormControl fullWidth>
              <InputLabel>מספר משתתפים מקסימלי</InputLabel>
              <Select label="מספר משתתפים מקסימלי" defaultValue={20}>
                <MenuItem value={10}>10 משתתפים</MenuItem>
                <MenuItem value={20}>20 משתתפים</MenuItem>
                <MenuItem value={30}>30 משתתפים</MenuItem>
                <MenuItem value={50}>50 משתתפים</MenuItem>
              </Select>
            </FormControl>
            <FormControl fullWidth>
              <InputLabel>אפשרויות</InputLabel>
              <Select label="אפשרויות" defaultValue="basic">
                <MenuItem value="basic">בסיסי</MenuItem>
                <MenuItem value="record">עם הקלטה</MenuItem>
                <MenuItem value="screen">שיתוף מסך</MenuItem>
                <MenuItem value="full">מלא - הקלטה + שיתוף</MenuItem>
              </Select>
            </FormControl>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenCreateDialog(false)}>ביטול</Button>
          <Button variant="contained" onClick={() => setOpenCreateDialog(false)}>
            צור חדר
          </Button>
        </DialogActions>
      </Dialog>
    </DashboardContent>
  );
}
