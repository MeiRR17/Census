import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';

// ----------------------------------------------------------------------

export function Background022() {
  return (
    <Box
      sx={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        zIndex: -1,
        background: 'linear-gradient(135deg, #E0F7FF 0%, #B3E5FC 50%, #81D4FA 100%)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        overflow: 'hidden',
      }}
    >
      <Typography
        sx={{
          fontSize: '50vw',
          fontWeight: 900,
          color: 'rgba(255, 50, 50, 0.15)',
          letterSpacing: '-0.05em',
          userSelect: 'none',
          lineHeight: 1,
          textShadow: '0 0 100px rgba(255, 100, 100, 0.3)',
        }}
      >
        022
      </Typography>
    </Box>
  );
}
