using System;

namespace GoToSleep.Models
{
    public class SleepSession
    {
        public DateTime StartTime { get; set; }
        public DateTime EndTime { get; set; }
        public int TotalMovements { get; set; }

        public string DurationDisplay
        {
            get
            {
                var span = EndTime - StartTime;
                return $"{span.Hours} jam {span.Minutes} menit {span.Seconds} detik";
            }
        }

        public string QualityDescription
        {
            get
            {
                // Logika sederhana: Sedikit gerak = Tidur nyenyak
                if (TotalMovements < 10) return "Sangat Nyenyak";
                if (TotalMovements < 50) return "Cukup Nyenyak";
                return "Gelisah / Banyak Gerak";
            }
        }
    }
}