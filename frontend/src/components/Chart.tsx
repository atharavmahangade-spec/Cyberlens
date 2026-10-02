import { useEffect, useRef } from 'react';
import * as echarts from 'echarts';
import { useTheme } from '@mui/material/styles';

export default function Chart({ option, height = 280 }: { option: echarts.EChartsOption; height?: number }) {
  const ref = useRef<HTMLDivElement>(null);
  const theme = useTheme();
  const key = JSON.stringify(option);
  useEffect(() => {
    const el = ref.current!;
    const c = echarts.init(el, theme.palette.mode === 'dark' ? 'dark' : undefined);
    c.setOption({ backgroundColor: 'transparent', textStyle: { fontFamily: theme.typography.fontFamily },
      color: [theme.palette.primary.main, '#ef6c00', '#2e7d32', '#8e24aa', '#6d7f94'], grid: { left: 48, right: 20, top: 36, bottom: 32 }, ...option });
    const ro = new ResizeObserver(() => c.resize());
    ro.observe(el);
    return () => { ro.disconnect(); c.dispose(); };
  }, [key, theme.palette.mode]);
  return <div ref={ref} style={{ height, width: '100%' }} />;
}
