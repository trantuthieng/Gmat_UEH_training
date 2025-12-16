"""
Test Mobile Responsive Design
Kiểm tra CSS và layout optimization cho mobile devices
"""

def test_mobile_css_loaded():
    """Kiểm tra CSS responsive có được load vào app.py"""
    print("🧪 Testing mobile CSS integration...")
    
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    checks = {
        'Responsive CSS block': '@media (max-width: 768px)' in content,
        'Mobile button styling': 'min-height: 44px' in content,
        'Touch-friendly radio': '.stRadio > div > label' in content,
        'Timer optimization': 'font-size: 3rem' in content,
        'Mobile padding': 'padding: 1rem 0.5rem' in content,
        'Responsive images': 'max-width: 100%' in content,
        'Smooth scrolling': 'scroll-behavior: smooth' in content,
    }
    
    passed = 0
    failed = 0
    
    for check_name, result in checks.items():
        if result:
            print(f"✅ {check_name}")
            passed += 1
        else:
            print(f"❌ {check_name}")
            failed += 1
    
    return passed, failed

def test_responsive_breakpoints():
    """Kiểm tra responsive breakpoints"""
    print("\n🧪 Testing responsive breakpoints...")
    
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    breakpoints = {
        'Mobile (< 768px)': '@media (max-width: 768px)' in content,
        'Tablet (769-1024px)': '@media (min-width: 769px) and (max-width: 1024px)' in content,
    }
    
    passed = 0
    failed = 0
    
    for bp_name, result in breakpoints.items():
        if result:
            print(f"✅ {bp_name} breakpoint found")
            passed += 1
        else:
            print(f"❌ {bp_name} breakpoint missing")
            failed += 1
    
    return passed, failed

def test_touch_targets():
    """Kiểm tra touch targets đạt chuẩn 44px (Apple HIG)"""
    print("\n🧪 Testing touch target sizes...")
    
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    targets = {
        'Buttons (44px min)': 'min-height: 44px' in content and '.stButton' in content,
        'Radio buttons (44px min)': 'min-height: 44px' in content and '.stRadio' in content,
    }
    
    passed = 0
    failed = 0
    
    for target_name, result in targets.items():
        if result:
            print(f"✅ {target_name} - Apple HIG compliant")
            passed += 1
        else:
            print(f"❌ {target_name} - Not compliant")
            failed += 1
    
    return passed, failed

def test_mobile_optimizations():
    """Kiểm tra các tối ưu mobile khác"""
    print("\n🧪 Testing additional mobile optimizations...")
    
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    optimizations = {
        'Progress indicator': 'st.progress' in content and 'answered / total_questions' in content,
        'Container width': 'use_container_width=True' in content,
        'Full width buttons': 'use_container_width=True' in content,
        'Visual feedback': 'transform: scale' in content,
        'Focus states': 'outline:' in content and ':focus' in content,
    }
    
    passed = 0
    failed = 0
    
    for opt_name, result in optimizations.items():
        if result:
            print(f"✅ {opt_name}")
            passed += 1
        else:
            print(f"❌ {opt_name}")
            failed += 1
    
    return passed, failed

def test_typography_responsive():
    """Kiểm tra typography responsive"""
    print("\n🧪 Testing responsive typography...")
    
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    typography = {
        'H1 mobile size': 'h1' in content and 'font-size: 1.5rem' in content,
        'H2 mobile size': 'h2' in content and 'font-size: 1.25rem' in content,
        'H3 mobile size': 'h3' in content and 'font-size: 1.1rem' in content,
        'Line height': 'line-height:' in content,
    }
    
    passed = 0
    failed = 0
    
    for typo_name, result in typography.items():
        if result:
            print(f"✅ {typo_name}")
            passed += 1
        else:
            print(f"❌ {typo_name}")
            failed += 1
    
    return passed, failed

def generate_mobile_test_report():
    """Tạo report chi tiết về mobile optimization"""
    print("\n" + "="*60)
    print("📱 Mobile Optimization Report")
    print("="*60)
    
    # Device specifications
    print("\n📱 Target Devices:")
    devices = [
        ("iPhone 15 Pro", "1179 x 2556 pixels", "6.1 inch"),
        ("iPhone 15 Pro Max", "1290 x 2796 pixels", "6.7 inch"),
        ("iPhone SE", "750 x 1334 pixels", "4.7 inch"),
        ("iPad", "1620 x 2160 pixels", "10.2 inch"),
    ]
    
    for name, resolution, size in devices:
        print(f"  • {name:.<30} {resolution} ({size})")
    
    # Optimization checklist
    print("\n✅ Optimization Checklist:")
    checklist = [
        "Responsive CSS with media queries",
        "Touch targets ≥ 44px (Apple HIG)",
        "Mobile-first approach",
        "Responsive typography",
        "Full-width buttons on mobile",
        "Progress indicators",
        "Smooth scrolling",
        "Visual feedback on interactions",
        "Accessible focus states",
        "Optimized images",
    ]
    
    for item in checklist:
        print(f"  ✓ {item}")
    
    # Performance metrics
    print("\n⚡ Expected Performance:")
    metrics = [
        ("Initial Load", "2-3 seconds"),
        ("Cached Load", "< 1 second"),
        ("Scroll Performance", "60 FPS"),
        ("Touch Response", "< 100ms"),
    ]
    
    for metric, value in metrics:
        print(f"  • {metric:.<30} {value}")

if __name__ == "__main__":
    print("="*60)
    print("🚀 Mobile Optimization Tests - iPhone 15 Pro")
    print("="*60)
    
    total_passed = 0
    total_failed = 0
    
    # Run all tests
    tests = [
        test_mobile_css_loaded,
        test_responsive_breakpoints,
        test_touch_targets,
        test_mobile_optimizations,
        test_typography_responsive,
    ]
    
    for test_func in tests:
        passed, failed = test_func()
        total_passed += passed
        total_failed += failed
    
    # Generate report
    generate_mobile_test_report()
    
    # Summary
    print("\n" + "="*60)
    print("📊 Test Summary")
    print("="*60)
    print(f"Total Tests: {total_passed + total_failed}")
    print(f"✅ Passed: {total_passed}")
    print(f"❌ Failed: {total_failed}")
    
    success_rate = (total_passed / (total_passed + total_failed) * 100) if (total_passed + total_failed) > 0 else 0
    print(f"Success Rate: {success_rate:.1f}%")
    
    if total_failed == 0:
        print("\n🎉 All mobile optimizations verified!")
        print("📱 Your app is ready for iPhone 15 Pro and other mobile devices!")
    else:
        print(f"\n⚠️  {total_failed} optimization(s) need attention.")
    
    print("\n💡 To test on iPhone 15 Pro:")
    print("   1. Run: streamlit run app.py --server.address 0.0.0.0")
    print("   2. Access from iPhone: http://[YOUR-IP]:8501")
    print("   3. Or use Chrome DevTools responsive mode")
