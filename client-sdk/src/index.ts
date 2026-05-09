/**
 * Census Client SDK - ספרייה ייעודית לאפליקציות קצה
 */

export interface Device {
  id?: number;
  name: string;
  ip_address?: string;
  mac_address?: string;
  device_type: string;
  status: string;
  source: string;
  raw_data?: any;
}

export interface User {
  id?: number;
  user_id: string;
  name: string;
  email?: string;
  department?: string;
  phone?: string;
  source: string;
  raw_data?: any;
}

export interface Meeting {
  id?: number;
  meeting_id: string;
  name: string;
  uri?: string;
  passcode?: string;
  status: string;
  participants: number;
  source: string;
  raw_data?: any;
}

export interface CreateDeviceData {
  name: string;
  ip_address?: string;
  mac_address?: string;
  device_type: string;
  status?: string;
  source: string;
  raw_data?: any;
}

export interface CreateUserData {
  user_id: string;
  name: string;
  email?: string;
  department?: string;
  phone?: string;
  source: string;
  raw_data?: any;
}

export interface CreateMeetingData {
  meeting_id: string;
  name: string;
  uri?: string;
  passcode?: string;
  status?: string;
  participants?: number;
  source: string;
  raw_data?: any;
}

export interface SyncStatus {
  connected_systems: string[];
  last_sync_times: Record<string, string>;
  system_status: Record<string, any>;
}

export class CensusClient {
  private baseURL: string;
  private headers: Record<string, string>;

  constructor(baseURL: string = 'http://localhost:8000') {
    this.baseURL = baseURL.replace(/\/$/, '');
    this.headers = {
      'Content-Type': 'application/json',
    };
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;
    const config: RequestInit = {
      headers: { ...this.headers, ...options.headers },
      ...options,
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`HTTP ${response.status}: ${errorText}`);
      }

      return await response.json();
    } catch (error) {
      if (error instanceof Error) {
        throw error;
      }
      throw new Error('Request failed');
    }
  }

  // ==================== פונקציות בריאות וסטטוס ====================

  /**
   * בדיקת סטטוס ה-API
   */
  async healthCheck(): Promise<any> {
    return this.request('/health');
  }

  // ==================== פונקציות מכשירים ====================

  /**
   * קבלת כל המכשירים
   */
  async getDevices(source?: string): Promise<Device[]> {
    const params = source ? `?source=${source}` : '';
    return this.request(`/api/devices${params}`);
  }

  /**
   * קבלת מכשיר ספציפי
   */
  async getDevice(name: string, source: string): Promise<Device | null> {
    const devices = await this.getDevices(source);
    return devices.find(d => d.name === name) || null;
  }

  /**
   * יצירת מכשיר חדש
   */
  async createDevice(deviceData: CreateDeviceData): Promise<Device> {
    return this.request('/api/devices', {
      method: 'POST',
      body: JSON.stringify(deviceData),
    });
  }

  /**
   * עדכון מכשיר קיים
   */
  async updateDevice(name: string, deviceData: Partial<CreateDeviceData>, source: string): Promise<Device> {
    // קודם קובע את המכשיר הקיים
    const existingDevice = await this.getDevice(name, source);
    if (!existingDevice) {
      throw new Error(`Device ${name} not found in ${source}`);
    }

    // מעדכן את המכשיר
    return this.request('/api/devices', {
      method: 'POST',
      body: JSON.stringify({
        ...existingDevice,
        ...deviceData,
        source,
      }),
    });
  }

  // ==================== פונקציות משתמשים ====================

  /**
   * קבלת כל המשתמשים
   */
  async getUsers(source?: string): Promise<User[]> {
    const params = source ? `?source=${source}` : '';
    return this.request(`/api/users${params}`);
  }

  /**
   * קבלת משתמש ספציפי
   */
  async getUser(userId: string, source: string): Promise<User | null> {
    const users = await this.getUsers(source);
    return users.find(u => u.user_id === userId) || null;
  }

  /**
   * יצירת משתמש חדש
   */
  async createUser(userData: CreateUserData): Promise<User> {
    return this.request('/api/users', {
      method: 'POST',
      body: JSON.stringify(userData),
    });
  }

  /**
   * עדכון משתמש קיים
   */
  async updateUser(userId: string, userData: Partial<CreateUserData>, source: string): Promise<User> {
    const existingUser = await this.getUser(userId, source);
    if (!existingUser) {
      throw new Error(`User ${userId} not found in ${source}`);
    }

    return this.request('/api/users', {
      method: 'POST',
      body: JSON.stringify({
        ...existingUser,
        ...userData,
        source,
      }),
    });
  }

  // ==================== פונקציות ועידות ====================

  /**
   * קבלת כל הוועידות
   */
  async getMeetings(source?: string): Promise<Meeting[]> {
    const params = source ? `?source=${source}` : '';
    return this.request(`/api/meetings${params}`);
  }

  /**
   * קבלת ועידה ספציפית
   */
  async getMeeting(meetingId: string, source: string): Promise<Meeting | null> {
    const meetings = await this.getMeetings(source);
    return meetings.find(m => m.meeting_id === meetingId) || null;
  }

  /**
   * יצירת ועידה חדשה
   */
  async createMeeting(meetingData: CreateMeetingData): Promise<Meeting> {
    return this.request('/api/meetings', {
      method: 'POST',
      body: JSON.stringify(meetingData),
    });
  }

  /**
   * עדכון ועידה קיימת
   */
  async updateMeeting(meetingId: string, meetingData: Partial<CreateMeetingData>, source: string): Promise<Meeting> {
    const existingMeeting = await this.getMeeting(meetingId, source);
    if (!existingMeeting) {
      throw new Error(`Meeting ${meetingId} not found in ${source}`);
    }

    return this.request('/api/meetings', {
      method: 'POST',
      body: JSON.stringify({
        ...existingMeeting,
        ...meetingData,
        source,
      }),
    });
  }

  // ==================== פונקציות סינכרון ====================

  /**
   * הפעלת סינכרון מלא
   */
  async triggerFullSync(): Promise<any> {
    return this.request('/api/sync', {
      method: 'POST',
    });
  }

  /**
   * הפעלת סינכרון למערכת ספציפית
   */
  async triggerSync(system?: string): Promise<any> {
    const endpoint = system ? `/api/sync?system=${system}` : '/api/sync';
    return this.request(endpoint, {
      method: 'POST',
    });
  }

  /**
   * קבלת סטטוס סינכרון
   */
  async getSyncStatus(): Promise<SyncStatus> {
    return this.request('/api/sync/status');
  }

  // ==================== פונקציות מתקדמות ====================

  /**
   * קבלת מכשירים מ-CUCM בלבד
   */
  async getCUCMDevices(): Promise<Device[]> {
    return this.getDevices('cucm');
  }

  /**
   * קבלת מכשירים מ-CMS בלבד
   */
  async getCMSDevices(): Promise<Device[]> {
    return this.getDevices('cms');
  }

  /**
   * קבלת משתמשים מ-CUCM בלבד
   */
  async getCUCMUsers(): Promise<User[]> {
    return this.getUsers('cucm');
  }

  /**
   * קבלת ועידות מ-CMS בלבד
   */
  async getCMSMeetings(): Promise<Meeting[]> {
    return this.getMeetings('cms');
  }

  /**
   * רישום טלפון חדש ב-CUCM
   */
  async registerPhone(data: {
    name: string;
    ip_address: string;
    mac_address: string;
    model?: string;
  }): Promise<Device> {
    return this.createDevice({
      name: data.name,
      ip_address: data.ip_address,
      mac_address: data.mac_address,
      device_type: data.model || 'Unknown',
      status: 'registered',
      source: 'cucm',
      raw_data: { model: data.model }
    });
  }

  /**
   * יצירת חדר ועידה חדש ב-CMS
   */
  async createMeetingRoom(data: {
    meeting_id: string;
    name: string;
    passcode?: string;
  }): Promise<Meeting> {
    return this.createMeeting({
      meeting_id: data.meeting_id,
      name: data.name,
      uri: data.meeting_id,
      passcode: data.passcode,
      status: 'active',
      participants: 0,
      source: 'cms'
    });
  }

  /**
   * קבלת סקירת מערכת מלאה
   */
  async getSystemOverview(): Promise<{
    devices: { total: number; online: number; offline: number; bySource: Record<string, number> };
    users: { total: number; bySource: Record<string, number> };
    meetings: { total: number; active: number; bySource: Record<string, number> };
    health: { status: string; connectedSystems: string[] };
  }> {
    try {
      const [devices, users, meetings, health, syncStatus] = await Promise.all([
        this.getDevices(),
        this.getUsers(),
        this.getMeetings(),
        this.healthCheck(),
        this.getSyncStatus()
      ]);

      const devicesBySource = devices.reduce((acc, device) => {
        acc[device.source] = (acc[device.source] || 0) + 1;
        return acc;
      }, {} as Record<string, number>);

      const usersBySource = users.reduce((acc, user) => {
        acc[user.source] = (acc[user.source] || 0) + 1;
        return acc;
      }, {} as Record<string, number>);

      const meetingsBySource = meetings.reduce((acc, meeting) => {
        acc[meeting.source] = (acc[meeting.source] || 0) + 1;
        return acc;
      }, {} as Record<string, number>);

      return {
        devices: {
          total: devices.length,
          online: devices.filter(d => d.status === 'online' || d.status === 'registered').length,
          offline: devices.filter(d => d.status === 'offline' || d.status === 'unregistered').length,
          bySource: devicesBySource
        },
        users: {
          total: users.length,
          bySource: usersBySource
        },
        meetings: {
          total: meetings.length,
          active: meetings.filter(m => m.status === 'active').length,
          bySource: meetingsBySource
        },
        health: {
          status: health.status || 'unknown',
          connectedSystems: syncStatus.connected_systems || []
        }
      };
    } catch (error) {
      throw new Error(`Failed to get system overview: ${error}`);
    }
  }
}

// Export default
export default CensusClient;
