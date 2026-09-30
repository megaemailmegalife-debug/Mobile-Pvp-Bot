package com.harvey.pvpagent;
public final class VisionPolicyCheck {
 static void pixel(byte[] frame,int w,int x,int y,int r,int g,int b){int i=(y*w+x)*4;frame[i]=(byte)r;frame[i+1]=(byte)g;frame[i+2]=(byte)b;frame[i+3]=(byte)255;}
 public static void main(String[] args){
  int w=256,h=144;byte[] frame=new byte[w*h*4];
  for(int y=0;y<h;y++)for(int x=0;x<w;x++)pixel(frame,w,x,y,40,70,100);
  if(VisionPolicy.detect(frame,w,h,0xffff0000).confidence!=0)throw new AssertionError("false positive");
  for(int y=55;y<83;y++)for(int x=165;x<195;x++)pixel(frame,w,x,y,220,30,20);
  VisionPolicy.Decision d=VisionPolicy.detect(frame,w,h,0xffff0000);
  if(!(d.confidence>.36f && d.dx>0 && Math.abs(d.dy)<.2f)) throw new AssertionError("target detection: "+d.confidence+"/"+d.dx+"/"+d.dy);
  System.out.println("VisionPolicy Java check passed: confidence="+d.confidence+", dx="+d.dx);
 }
}
