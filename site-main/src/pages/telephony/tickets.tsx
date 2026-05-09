import { useState } from 'react';

import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import Grid from '@mui/material/Grid';
import Chip from '@mui/material/Chip';
import Button from '@mui/material/Button';
import Dialog from '@mui/material/Dialog';
import Select from '@mui/material/Select';
import MenuItem from '@mui/material/MenuItem';
import Table from '@mui/material/Table';
import TableRow from '@mui/material/TableRow';
import TableHead from '@mui/material/TableHead';
import TableCell from '@mui/material/TableCell';
import TableBody from '@mui/material/TableBody';
import Typography from '@mui/material/Typography';
import CardContent from '@mui/material/CardContent';
import TextField from '@mui/material/TextField';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import FormControl from '@mui/material/FormControl';
import InputLabel from '@mui/material/InputLabel';
import IconButton from '@mui/material/IconButton';

import { DashboardContent } from 'src/layouts/dashboard';
import { Iconify } from 'src/components/iconify';

// ----------------------------------------------------------------------

const TICKETS = [
  { id: 'INC-2024-001', subject: 'בעיה בהפניית שיחות', category: 'תקלה', status: 'open', priority: 'high', created: '2024-01-15', updated: '2024-01-15' },
  { id: 'INC-2024-002', subject: 'בקשה לשינוי שלוחה', category: 'בקשה', status: 'in_progress', priority: 'medium', created: '2024-01-14', updated: '2024-01-15' },
  { id: 'INC-2024-003', subject: 'איפוס סיסמת תא קולי', category: 'שירות', status: 'closed', priority: 'low', created: '2024-01-10', updated: '2024-01-12' },
  { id: 'INC-2024-004', subject: 'עדכון כתובת MAC', category: 'בקשה', status: 'closed', priority: 'medium', created: '2024-01-08', updated: '2024-01-09' },
];

const getStatusColor = (status: string) => {
  switch (status) {
    case 'open':
      return 'error';
    case 'in_progress':
      return 'warning';
    case 'closed':
      return 'success';
    default:
      return 'default';
  }
};

const getStatusLabel = (status: string) => {
  switch (status) {
    case 'open':
      return 'פתוח';
    case 'in_progress':
      return 'בטיפול';
    case 'closed':
      return 'סגור';
    default:
      return status;
  }
};

const getPriorityColor = (priority: string) => {
  switch (priority) {
    case 'high':
      return 'error';
    case 'medium':
      return 'warning';
    case 'low':
      return 'info';
    default:
      return 'default';
  }
};

const getPriorityLabel = (priority: string) => {
  switch (priority) {
    case 'high':
      return 'דחוף';
    case 'medium':
      return 'בינוני';
    case 'low':
      return 'נמוך';
    default:
      return priority;
  }
};

export default function TicketsPage() {
  const [openDialog, setOpenDialog] = useState(false);

  return (
    <DashboardContent maxWidth="xl">
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">קריאות תמיכה</Typography>
        <Button
          variant="contained"
          startIcon={<Iconify icon="mingcute:add-line" />}
          onClick={() => setOpenDialog(true)}
        >
          קריאה חדשה
        </Button>
      </Box>

      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h3" color="error.main">
                1
              </Typography>
              <Typography variant="body2" color="text.secondary">
                קריאות פתוחות
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h3" color="warning.main">
                1
              </Typography>
              <Typography variant="body2" color="text.secondary">
                בטיפול
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h3" color="success.main">
                2
              </Typography>
              <Typography variant="body2" color="text.secondary">
                סגורים החודש
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h3" color="info.main">
                95%
              </Typography>
              <Typography variant="body2" color="text.secondary">
                שביעות רצון
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Card>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>מספר קריאה</TableCell>
              <TableCell>נושא</TableCell>
              <TableCell>קטגוריה</TableCell>
              <TableCell>סטטוס</TableCell>
              <TableCell>עדיפות</TableCell>
              <TableCell>נוצר</TableCell>
              <TableCell>עודכן</TableCell>
              <TableCell align="center">פעולות</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {TICKETS.map((ticket) => (
              <TableRow key={ticket.id} hover>
                <TableCell>
                  <Typography variant="subtitle2">{ticket.id}</Typography>
                </TableCell>
                <TableCell>{ticket.subject}</TableCell>
                <TableCell>{ticket.category}</TableCell>
                <TableCell>
                  <Chip
                    size="small"
                    color={getStatusColor(ticket.status) as any}
                    label={getStatusLabel(ticket.status)}
                  />
                </TableCell>
                <TableCell>
                  <Chip
                    size="small"
                    color={getPriorityColor(ticket.priority) as any}
                    label={getPriorityLabel(ticket.priority)}
                    variant="outlined"
                  />
                </TableCell>
                <TableCell>{ticket.created}</TableCell>
                <TableCell>{ticket.updated}</TableCell>
                <TableCell align="center">
                  <IconButton color="primary" size="small">
                    <Iconify icon="solar:eye-bold" />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Card>

      {/* New Ticket Dialog */}
      <Dialog open={openDialog} onClose={() => setOpenDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>פתיחת קריאת תמיכה חדשה</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1 }}>
            <FormControl fullWidth>
              <InputLabel>קטגוריה</InputLabel>
              <Select label="קטגוריה" defaultValue="">
                <MenuItem value="">בחר קטגוריה</MenuItem>
                <MenuItem value="issue">תקלה</MenuItem>
                <MenuItem value="request">בקשה</MenuItem>
                <MenuItem value="service">שירות</MenuItem>
              </Select>
            </FormControl>
            <TextField label="נושא" fullWidth />
            <TextField label="תיאור" multiline rows={4} fullWidth />
            <FormControl fullWidth>
              <InputLabel>עדיפות</InputLabel>
              <Select label="עדיפות" defaultValue="medium">
                <MenuItem value="low">נמוך</MenuItem>
                <MenuItem value="medium">בינוני</MenuItem>
                <MenuItem value="high">דחוף</MenuItem>
              </Select>
            </FormControl>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenDialog(false)}>ביטול</Button>
          <Button variant="contained" onClick={() => setOpenDialog(false)}>
            פתח קריאה
          </Button>
        </DialogActions>
      </Dialog>
    </DashboardContent>
  );
}
