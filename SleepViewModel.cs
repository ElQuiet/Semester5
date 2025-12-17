
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using GoToSleep.Models;
using System.Numerics;

namespace GoToSleep.ViewModels
{
    public partial class SleepViewModel : ObservableObject
    {
        // Variabel untuk tampilan (UI)
        [ObservableProperty]
        private string statusMessage = "Tekan Mulai untuk memonitor";

        [ObservableProperty]
        private string buttonText = "Mulai Tidur";

        [ObservableProperty]
        private bool isTracking = false;

        [ObservableProperty]
        private string lastResult = "-";

        // Variabel internal logic
        private int _movementCount = 0;
        private DateTime _startInfo;

        // Fisika: Gravitasi bumi itu 1.0g.
        // Jika HP diam, resultan gayanya ~1.0. Jika bergerak, nilainya berubah.
        private const double MovementThreshold = 0.07; // Sensitivitas

        [RelayCommand]
        void ToggleTracking()
        {
            if (IsTracking)
                StopSensor();
            else
                StartSensor();
        }

        private void StartSensor()
        {
            if (Accelerometer.Default.IsSupported)
            {
                if (!Accelerometer.Default.IsMonitoring)
                {
                    _movementCount = 0;
                    _startInfo = DateTime.Now;

                    // Event saat sensor berubah data
                    Accelerometer.Default.ReadingChanged += OnReadingChanged;
                    // SensorSpeed.UI cukup lambat (60ms) hemat baterai
                    Accelerometer.Default.Start(SensorSpeed.UI);

                    IsTracking = true;
                    ButtonText = "Bangun / Stop";
                    StatusMessage = "Memonitor... Zzz...";
                }
            }
            else
            {
                StatusMessage = "Maaf, Sensor Accelerometer tidak didukung di alat ini.";
            }
        }

        private void StopSensor()
        {
            if (Accelerometer.Default.IsSupported)
            {
                Accelerometer.Default.Stop();
                Accelerometer.Default.ReadingChanged -= OnReadingChanged;
            }

            IsTracking = false;
            ButtonText = "Mulai Tidur";

            // Simpan hasil ke model
            var session = new SleepSession
            {
                StartTime = _startInfo,
                EndTime = DateTime.Now,
                TotalMovements = _movementCount
            };

            StatusMessage = "Monitoring Selesai.";
            LastResult = $"Durasi: {session.DurationDisplay}\n" +
                         $"Gerakan: {session.TotalMovements} kali\n" +
                         $"Kualitas: {session.QualityDescription}";
        }

        private void OnReadingChanged(object sender, AccelerometerChangedEventArgs e)
        {
            var data = e.Reading.Acceleration;

            // Rumus Magnitude Vektor: V = sqrt(x^2 + y^2 + z^2)
            float magnitude = (float)Math.Sqrt(data.X * data.X + data.Y * data.Y + data.Z * data.Z);

            // Deteksi penyimpangan dari gravitasi (1.0)
            double deviation = Math.Abs(magnitude - 1.0);

            if (deviation > MovementThreshold)
            {
                _movementCount++;
                // Update UI sesekali (opsional, jangan terlalu sering agar tidak lag)
                StatusMessage = $"Terdeteksi Gerak: {_movementCount}";
            }
        }
    }
}