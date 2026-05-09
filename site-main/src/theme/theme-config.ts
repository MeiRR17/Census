import type { CommonColors } from '@mui/material/styles';

import type { ThemeCssVariables } from './types';
import type { PaletteColorNoChannels } from './core/palette';

// ----------------------------------------------------------------------

type ThemeConfig = {
  classesPrefix: string;
  cssVariables: ThemeCssVariables;
  fontFamily: Record<'primary' | 'secondary', string>;
  palette: Record<
    'primary' | 'secondary' | 'info' | 'success' | 'warning' | 'error',
    PaletteColorNoChannels
  > & {
    common: Pick<CommonColors, 'black' | 'white'>;
    grey: Record<
      '50' | '100' | '200' | '300' | '400' | '500' | '600' | '700' | '800' | '900',
      string
    >;
  };
};

export const themeConfig: ThemeConfig = {
  /** **************************************
   * Base
   *************************************** */
  classesPrefix: 'minimal',
  /** **************************************
   * Typography
   *************************************** */
  fontFamily: {
    primary: 'DM Sans Variable',
    secondary: 'Barlow',
  },
  /** **************************************
   * Palette
   *************************************** */
  palette: {
    primary: {
      lighter: '#E0F7FF',
      light: '#4FC3F7',
      main: '#0288D1',
      dark: '#01579B',
      darker: '#003C6C',
      contrastText: '#FFFFFF',
    },
    secondary: {
      lighter: '#FFEBEE',
      light: '#EF5350',
      main: '#D32F2F',
      dark: '#C62828',
      darker: '#B71C1C',
      contrastText: '#FFFFFF',
    },
    info: {
      lighter: '#E0F7FF',
      light: '#4FC3F7',
      main: '#0288D1',
      dark: '#01579B',
      darker: '#003C6C',
      contrastText: '#FFFFFF',
    },
    success: {
      lighter: '#E8F5E9',
      light: '#66BB6A',
      main: '#43A047',
      dark: '#2E7D32',
      darker: '#1B5E20',
      contrastText: '#ffffff',
    },
    warning: {
      lighter: '#FFF3E0',
      light: '#FFB74D',
      main: '#FF9800',
      dark: '#F57C00',
      darker: '#E65100',
      contrastText: '#1C252E',
    },
    error: {
      lighter: '#FFEBEE',
      light: '#EF5350',
      main: '#D32F2F',
      dark: '#C62828',
      darker: '#B71C1C',
      contrastText: '#FFFFFF',
    },
    grey: {
      '50': '#FAFAFA',
      '100': '#F5F5F5',
      '200': '#EEEEEE',
      '300': '#E0E0E0',
      '400': '#BDBDBD',
      '500': '#9E9E9E',
      '600': '#757575',
      '700': '#616161',
      '800': '#424242',
      '900': '#212121',
    },
    common: { black: '#000000', white: '#FFFFFF' },
  },
  /** **************************************
   * Css variables
   *************************************** */
  cssVariables: {
    cssVarPrefix: '',
    colorSchemeSelector: 'data-color-scheme',
  },
};
