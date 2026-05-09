import { useState } from 'react';

import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import Grid from '@mui/material/Grid';
import Table from '@mui/material/Table';
import Button from '@mui/material/Button';
import TableRow from '@mui/material/TableRow';
import TableHead from '@mui/material/TableHead';
import TableCell from '@mui/material/TableCell';
import TableBody from '@mui/material/TableBody';
import Typography from '@mui/material/Typography';
import CardContent from '@mui/material/CardContent';
import TextField from '@mui/material/TextField';
import InputAdornment from '@mui/material/InputAdornment';
import Avatar from '@mui/material/Avatar';
import IconButton from '@mui/material/IconButton';

import { DashboardContent } from 'src/layouts/dashboard';
import { Iconify } from 'src/components/iconify';

// ----------------------------------------------------------------------

const DIRECTORY_DATA = [
  { id: 1, name: 'דני דן', extension: '1001', department: 'מחלקת IT', phone: '02-5551001', email: 'dani@company.com', status: 'online' },
  { id: 2, name: 'יוסי לוי', extension: '1002', department: 'משאבי אנוש', phone: '02-5551002', email: 'yossi@company.com', status: 'offline' },
  { id: 3, name: 'שרה כהן', extension: '1003', department: 'כספים', phone: '02-5551003', email: 'sarah@company.com', status: 'online' },
  { id: 4, name: 'משה רבינו', extension: '1004', department: 'מכירות', phone: '02-5551004', email: 'moshe@company.com', status: 'busy' },
  { id: 5, name: 'רחל גרין', extension: '1005', department: 'שיווק', phone: '02-5551005', email: 'rachel@company.com', status: 'online' },
  { id: 6, name: 'אבי כהן', extension: '1006', department: 'מחלקת IT', phone: '02-5551006', email: 'avi@company.com', status: 'offline' },
  { id: 7, name: 'מיכל לוי', extension: '1007', department: 'משאבי אנוש', phone: '02-5551007', email: 'michal@company.com', status: 'online' },
  { id: 8, name: 'דוד פרץ', extension: '1008', department: 'כספים', phone: '02-5551008', email: 'david@company.com', status: 'online' },
];

const getStatusColor = (status: string) => {
  switch (status) {
    case 'online':
      return 'success';
    case 'busy':
      return 'warning';
    case 'offline':
      return 'default';
    default:
      return 'default';
  }
};

const getStatusLabel = (status: string) => {
  switch (status) {
    case 'online':
      return 'זמין';
    case 'busy':
      return 'תפוס';
    case 'offline':
      return 'לא זמין';
    default:
      return status;
  }
};

export default function DirectoryPage() {
  const [searchQuery, setSearchQuery] = useState('');

  const filteredData = DIRECTORY_DATA.filter(
    (item) =>
      item.name.includes(searchQuery) ||
      item.extension.includes(searchQuery) ||
      item.department.includes(searchQuery) ||
      item.phone.includes(searchQuery)
  );

  return (
    <DashboardContent maxWidth="xl">
      <Typography variant="h4" sx={{ mb: 3 }}>
        ספר טלפונים ארגוני
      </Typography>

      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2} alignItems="center">
            <Grid size={{ xs: 12, md: 6 }}>
              <TextField
                fullWidth
                placeholder="חיפוש לפי שם, שלוחה, מחלקה או טלפון..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <Iconify icon="eva:search-fill" />
                    </InputAdornment>
                  ),
                }}
              />
            </Grid>
            <Grid size={{ xs: 12, md: 6 }}>
              <Box sx={{ display: 'flex', gap: 1, justifyContent: { md: 'flex-end' } }}>
                <Button variant="outlined" startIcon={<Iconify icon="solar:users-group-rounded-bold-duotone" />}>
                  המחלקה שלי
                </Button>
                <Button variant="outlined" startIcon={<Iconify icon="solar:user-id-bold-duotone" />}>
                  נפוץ
                </Button>
              </Box>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      <Card>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>שם</TableCell>
              <TableCell>שלוחה</TableCell>
              <TableCell>מחלקה</TableCell>
              <TableCell>טלפון</TableCell>
              <TableCell>מצב</TableCell>
              <TableCell align="center">פעולות</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredData.map((row) => (
              <TableRow key={row.id} hover>
                <TableCell>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                    <Avatar sx={{ width: 32, height: 32, bgcolor: 'primary.main' }}>
                      {row.name.charAt(0)}
                    </Avatar>
                    <Box>
                      <Typography variant="subtitle2">{row.name}</Typography>
                      <Typography variant="caption" color="text.secondary">
                        {row.email}
                      </Typography>
                    </Box>
                  </Box>
                </TableCell>
                <TableCell>
                  <Typography variant="body2" fontWeight="bold">
                    {row.extension}
                  </Typography>
                </TableCell>
                <TableCell>{row.department}</TableCell>
                <TableCell dir="ltr">{row.phone}</TableCell>
                <TableCell>
                  <Box
                    component="span"
                    sx={{
                      px: 1,
                      py: 0.5,
                      borderRadius: 1,
                      fontSize: '0.75rem',
                      fontWeight: 'bold',
                      bgcolor: `${getStatusColor(row.status)}.lighter`,
                      color: `${getStatusColor(row.status)}.dark`,
                    }}
                  >
                    {getStatusLabel(row.status)}
                  </Box>
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
