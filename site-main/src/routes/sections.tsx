import type { RouteObject } from 'react-router';

import { lazy, Suspense } from 'react';
import { Outlet } from 'react-router-dom';
import { varAlpha } from 'minimal-shared/utils';

import Box from '@mui/material/Box';
import LinearProgress, { linearProgressClasses } from '@mui/material/LinearProgress';

import { TelephonyLayout } from 'src/layouts/telephony';

// ----------------------------------------------------------------------

export const DashboardPage = lazy(() => import('src/pages/telephony/dashboard'));
export const DirectoryPage = lazy(() => import('src/pages/telephony/directory'));
export const CallHistoryPage = lazy(() => import('src/pages/telephony/call-history'));
export const TicketsPage = lazy(() => import('src/pages/telephony/tickets'));
export const SettingsPage = lazy(() => import('src/pages/telephony/settings'));
export const Page404 = lazy(() => import('src/pages/page-not-found'));

const renderFallback = () => (
  <Box
    sx={{
      display: 'flex',
      flex: '1 1 auto',
      alignItems: 'center',
      justifyContent: 'center',
    }}
  >
    <LinearProgress
      sx={{
        width: 1,
        maxWidth: 320,
        bgcolor: (theme) => varAlpha(theme.vars.palette.text.primaryChannel, 0.16),
        [`& .${linearProgressClasses.bar}`]: { bgcolor: 'text.primary' },
      }}
    />
  </Box>
);

export const routesSection: RouteObject[] = [
  {
    element: (
      <TelephonyLayout>
        <Suspense fallback={renderFallback()}>
          <Outlet />
        </Suspense>
      </TelephonyLayout>
    ),
    children: [
      { index: true, element: <DashboardPage /> },
      { path: 'directory', element: <DirectoryPage /> },
      { path: 'calls', element: <CallHistoryPage /> },
      { path: 'tickets', element: <TicketsPage /> },
      { path: 'settings', element: <SettingsPage /> },
    ],
  },
  {
    path: '404',
    element: <Page404 />,
  },
  { path: '*', element: <Page404 /> },
];
