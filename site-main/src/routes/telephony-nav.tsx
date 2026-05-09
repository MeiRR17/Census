import { Iconify } from 'src/components/iconify';
import { RouterLink } from 'src/routes/components';
import type { IconifyName } from 'src/components/iconify';

// ----------------------------------------------------------------------

export type NavItem = {
  title: string;
  path: string;
  icon: IconifyName;
  info?: React.ReactNode;
  children?: NavItem[];
};

const icon = (name: IconifyName) => (
  <Iconify icon={name} width={24} />
);

export const telephonyNavData: NavItem[] = [
  {
    title: 'מסך ראשי',
    path: '/',
    icon: 'solar:home-angle-bold-duotone',
  },
  {
    title: 'ספר טלפונים',
    path: '/directory',
    icon: 'solar:address-book-bold-duotone',
  },
  {
    title: 'היסטוריית שיחות',
    path: '/calls',
    icon: 'solar:phone-bold-duotone',
  },
  {
    title: 'קריאות תמיכה',
    path: '/tickets',
    icon: 'solar:headphones-round-sound-bold-duotone',
  },
  {
    title: 'הגדרות מערכת',
    path: '/settings',
    icon: 'solar:settings-bold-duotone',
  },
];
