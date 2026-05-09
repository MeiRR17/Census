import { useState } from 'react';

import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import Chip from '@mui/material/Chip';
import Table from '@mui/material/Table';
import Button from '@mui/material/Button';
import TableRow from '@mui/material/TableRow';
import TableHead from '@mui/material/TableHead';
import TableCell from '@mui/material/TableCell';
import TableBody from '@mui/material/TableBody';
import Typography from '@mui/material/Typography';
import CardContent from '@mui/material/CardContent';
import IconButton from '@mui/material/IconButton';
import Tabs from '@mui/material/Tabs';
import Tab from '@mui/material/Tab';
import Avatar from '@mui/material/Avatar';

import { DashboardContent } from 'src/layouts/dashboard';
import { Iconify } from 'src/components/iconify';

// ----------------------------------------------------------------------

const CALL_HISTORY = [
  { id: 1, name: 'ישראל ישראלי', number: '1002', duration: '02:35', time: '10:23', date: '2024-01-15', type: 'incoming', status: 'answered' },
  { id: 2, name: 'שרה כהן', number: '1005', duration: '01:12', time: '09:45', date: '2024-01-15', type: 'outgoing', status: 'answered' },
  { id: 3, name: 'דני לוי', number: '1003', duration: '-', time: '09:12', date: '2024-01-15', type: 'missed', status: 'missed' },
  { id: 4, name: 'מיכל בר', number: '054-1234567', duration: '05:22', time: '16:30', date: '2024-01-14', type: 'outgoing', status: 'answered' },
  { id: 5, name: 'אלמוני', number: '03-1234567', duration: '-', time: '14:15', date: '2024-01-14', type: 'missed', status: 'missed' },
  { id: 6, name: 'רוני כהן', number: '1008', duration: '00:45', time: '11:20', date: '2024-01-14', type: 'incoming', status: 'answered' },
];

const getTypeIcon = (type: string) => {
  switch (type) {
    case 'incoming':
      return 'solar:incoming-call-rounded-bold-duotone';
    case 'outgoing':
      return 'solar:outgoing-call-rounded-bold-duotone';
    case 'missed':
      return 'solar:call-dropped-bold-duotone';
    default:
      return 'solar:phone-bold-duotone';
  }
};

const getTypeColor = (type: string) => {
  switch (type) {
    case 'incoming':
      return 'success';
    case 'outgoing':
      return 'info';
    case 'missed':
      return 'error';
    default:
      return 'default';
  }
};

const getTypeLabel = (type: string) => {
  switch (type) {
    case 'incoming':
      return 'נכנסת';
    case 'outgoing':
      return 'יוצאת';
    case 'missed':
      return 'לא נענתה';
    default:
      return type;
  }
};

export default function CallHistoryPage() {
  const [tabValue, setTabValue] = useState(0);

  const filteredCalls = CALL_HISTORY.filter((call) => {
    if (tabValue === 0) return true;
    if (tabValue === 1) return call.type === 'incoming';
    if (tabValue === 2) return call.type === 'outgoing';
    if (tabValue === 3) return call.type === 'missed';
    return true;
  });

  return (
    <DashboardContent maxWidth="xl">
      <Typography variant="h4" sx={{ mb: 3 }}>
        היסטוריית שיחות
      </Typography>

      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6">סינון שיחות</Typography>
            <Button variant="outlined" startIcon={<Iconify icon="solar:restart-bold" />}>
              רענון
            </Button>
          </Box>
          <Tabs
            value={tabValue}
            onChange={(e, newValue) => setTabValue(newValue)}
            textColor="primary"
            indicatorColor="primary"
          >
            <Tab label="הכל" />
            <Tab label="נכנסות" />
            <Tab label="יוצאות" />
            <Tab label="לא נענו" />
          </Tabs>
        </CardContent>
      </Card>

      <Card>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>סוג</TableCell>
              <TableCell>שם/מספר</TableCell>
              <TableCell>תאריך</TableCell>
              <TableCell>שעה</TableCell>
              <TableCell>משך</TableCell>
              <TableCell align="center">פעולות</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredCalls.map((call) => (
              <TableRow key={call.id} hover>
                <TableCell>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Iconify
                      icon={getTypeIcon(call.type)}
                      sx={{ color: `${getTypeColor(call.type)}.main`, fontSize: 24 }}
                    />
                    <Chip
                      size="small"
                      color={getTypeColor(call.type) as any}
                      label={getTypeLabel(call.type)}
                    />
                  </Box>
                </TableCell>
                <TableCell>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                    <Avatar sx={{ width: 32, height: 32, bgcolor: 'primary.main' }}>
                      {call.name.charAt(0)}
                    </Avatar>
                    <Box>
                      <Typography variant="subtitle2">{call.name}</Typography>
                      <Typography variant="caption" color="text.secondary" dir="ltr">
                        {call.number}
                      </Typography>
                    </Box>
                  </Box>
                </TableCell>
                <TableCell>{call.date}</TableCell>
                <TableCell>{call.time}</TableCell>
                <TableCell>
                  <Typography
                    variant="body2"
                    color={call.duration === '-' ? 'error' : 'text.primary'}
                  >
                    {call.duration === '-' ? '-' : call.duration}
                  </Typography>
                </TableCell>
                <TableCell align="center">
                  <IconButton color="primary" size="small">
                    <Iconify icon="solar:phone-bold-duotone" />
                  </IconButton>
                  <IconButton color="info" size="small">
                    <Iconify icon="solar:chat-round-dots-bold" />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Card>
    </DashboardContent>
  );
}
