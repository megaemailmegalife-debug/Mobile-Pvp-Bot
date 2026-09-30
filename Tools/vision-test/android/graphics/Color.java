package android.graphics;
public final class Color {
 public static void colorToHSV(int c, float[] out) { RGBToHSV((c>>16)&255,(c>>8)&255,c&255,out); }
 public static void RGBToHSV(int r,int g,int b,float[] out) {
  float rf=r/255f,gf=g/255f,bf=b/255f;
  float max=Math.max(rf,Math.max(gf,bf)),min=Math.min(rf,Math.min(gf,bf)),d=max-min;
  float hue=0;
  if(d!=0) { if(max==rf) hue=60*((gf-bf)/d%6); else if(max==gf) hue=60*((bf-rf)/d+2); else hue=60*((rf-gf)/d+4); }
  out[0]=hue<0?hue+360:hue;out[1]=max==0?0:d/max;out[2]=max;
 }
}
