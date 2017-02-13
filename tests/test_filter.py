import lemoncheesecake as lcc
from lemoncheesecake.testsuite.filter import Filter

from helpers import run_testsuite, reporting_session

def test_filter_full_path_on_test(reporting_session):
    class mysuite(lcc.TestSuite):
        class subsuite(lcc.TestSuite):
            @lcc.test("test1")
            def baz(self):
                pass
            
            @lcc.test("test2")
            def test2(self):
                pass

    filter = Filter()
    filter.path.append("mysuite.subsuite.baz")
    
    run_testsuite(mysuite, filter=filter)
    
    assert reporting_session.test_nb == 1
    assert reporting_session.last_test == "baz"

def test_filter_full_path_on_test_negative(reporting_session):
    class mysuite(lcc.TestSuite):
        class subsuite(lcc.TestSuite):
            @lcc.test("test1")
            def baz(self):
                pass
            
            @lcc.test("test2")
            def test2(self):
                pass

    filter = Filter()
    filter.path.append("-mysuite.subsuite.baz")
    
    run_testsuite(mysuite, filter=filter)
    
    assert reporting_session.test_nb == 1
    assert reporting_session.last_test == "test2"

def test_filter_path_on_suite(reporting_session):
    class mysuite(lcc.TestSuite):
        class subsuite(lcc.TestSuite):
            @lcc.test("test1")
            def baz(self):
                pass
            
            @lcc.test("test2")
            def test2(self):
                pass

    filter = Filter()
    filter.path.append("mysuite.subsuite")
    
    run_testsuite(mysuite, filter=filter)
    
    assert reporting_session.test_nb == 2

def test_filter_path_on_suite_negative(reporting_session):
    class mysuite(lcc.TestSuite):
        class subsuite(lcc.TestSuite):
            @lcc.test("test1")
            def baz(self):
                pass
            
            @lcc.test("test2")
            def test2(self):
                pass

    filter = Filter()
    filter.path.append("-mysuite.subsuite.*")
    
    run_testsuite(mysuite, filter=filter)
    
    assert reporting_session.test_nb == 0

def test_filter_path_complete_on_top_suite(reporting_session):
    class mysuite(lcc.TestSuite):
        class subsuite(lcc.TestSuite):
            @lcc.test("test1")
            def baz(self):
                pass
            
            @lcc.test("test2")
            def test2(self):
                pass

    filter = Filter()
    filter.path.append("mysuite")
    
    run_testsuite(mysuite, filter=filter)
    
    assert reporting_session.test_nb == 2

def test_filter_path_wildcard_on_test(reporting_session):
    class mysuite(lcc.TestSuite):
        class subsuite(lcc.TestSuite):
            @lcc.test("test1")
            def baz(self):
                pass
            
            @lcc.test("test2")
            def test2(self):
                pass

    filter = Filter()
    filter.path.append("mysuite.subsuite.ba*")
    
    run_testsuite(mysuite, filter=filter)
    
    assert reporting_session.test_nb == 1
    assert reporting_session.last_test == "baz"

def test_filter_path_wildcard_on_test_negative(reporting_session):
    class mysuite(lcc.TestSuite):
        class subsuite(lcc.TestSuite):
            @lcc.test("test1")
            def baz(self):
                pass
            
            @lcc.test("test2")
            def test2(self):
                pass

    filter = Filter()
    filter.path.append("-mysuite.subsuite.ba*")
    
    run_testsuite(mysuite, filter=filter)
    
    assert reporting_session.test_nb == 1
    assert reporting_session.last_test == "test2"

def test_filter_path_wildcard_on_suite(reporting_session):
    class mysuite(lcc.TestSuite):
        class subsuite(lcc.TestSuite):
            @lcc.test("test1")
            def baz(self):
                pass
            
            @lcc.test("test2")
            def test2(self):
                pass

    filter = Filter()
    filter.path.append("mysuite.sub*.baz")
    
    run_testsuite(mysuite, filter=filter)
    
    assert reporting_session.test_nb == 1
    assert reporting_session.last_test == "baz"

def test_filter_path_wildcard_on_suite_negative(reporting_session):
    class mysuite(lcc.TestSuite):
        class subsuite(lcc.TestSuite):
            @lcc.test("test1")
            def baz(self):
                pass
            
            @lcc.test("test2")
            def test2(self):
                pass

    filter = Filter()
    filter.path.append("-mysuite.sub*.baz")
    
    run_testsuite(mysuite, filter=filter)
    
    assert reporting_session.test_nb == 1
    assert reporting_session.last_test == "test2"

def test_filter_description_on_test(reporting_session):
    class mysuite(lcc.TestSuite):
        class subsuite(lcc.TestSuite):
            @lcc.test("desc1")
            def baz(self):
                pass
            
            @lcc.test("desc2")
            def test2(self):
                pass
    
    filter = Filter()
    filter.description.append("desc2")
    
    run_testsuite(mysuite, filter=filter)
    
    assert reporting_session.test_nb == 1
    assert reporting_session.last_test == "test2"    

def test_filter_description_on_test_negative(reporting_session):
    class mysuite(lcc.TestSuite):
        class subsuite(lcc.TestSuite):
            @lcc.test("desc1")
            def baz(self):
                pass
            
            @lcc.test("desc2")
            def test2(self):
                pass
    
    filter = Filter()
    filter.description.append("-desc2")
    
    run_testsuite(mysuite, filter=filter)
    
    assert reporting_session.test_nb == 1
    assert reporting_session.last_test == "baz"    

def test_filter_description_on_suite(reporting_session):
    class mysuite(lcc.TestSuite):
        class subsuite(lcc.TestSuite):
            description = "desc1"
            
            @lcc.test("baz")
            def baz(self):
                pass
        
        class othersuite(lcc.TestSuite):
            description = "desc2"
            
            @lcc.test("test2")
            def test2(self):
                pass
    
    filter = Filter()
    filter.description.append("desc2")
    
    run_testsuite(mysuite, filter=filter)
    
    assert reporting_session.test_nb == 1
    assert reporting_session.last_test == "test2"

def test_filter_description_on_suite_negative(reporting_session):
    class mysuite(lcc.TestSuite):
        class subsuite(lcc.TestSuite):
            description = "desc1"
            
            @lcc.test("baz")
            def baz(self):
                pass
        
        class othersuite(lcc.TestSuite):
            description = "desc2"
            
            @lcc.test("test2")
            def test2(self):
                pass
    
    filter = Filter()
    filter.description.append("-desc2")
    
    run_testsuite(mysuite, filter=filter)
    
    assert reporting_session.test_nb == 1
    assert reporting_session.last_test == "baz"

def test_filter_tag_on_test(reporting_session):
    class mysuite(lcc.TestSuite):
        class subsuite(lcc.TestSuite):
            @lcc.test("test1")
            def baz(self):
                pass
            
            @lcc.tags("tag1")
            @lcc.test("test2")
            def test2(self):
                pass

    filter = Filter()
    filter.tags.append("tag1")
    
    run_testsuite(mysuite, filter=filter)
    
    assert reporting_session.test_nb == 1
    assert reporting_session.last_test == "test2"

def test_filter_tag_on_test_negative(reporting_session):
    class mysuite(lcc.TestSuite):
        class subsuite(lcc.TestSuite):
            @lcc.test("test1")
            def baz(self):
                pass
            
            @lcc.tags("tag1")
            @lcc.test("test2")
            def test2(self):
                pass

    filter = Filter()
    filter.tags.append("-tag1")
    
    run_testsuite(mysuite, filter=filter)
    
    assert reporting_session.test_nb == 1
    assert reporting_session.last_test == "baz"

def test_filter_tag_on_suite(reporting_session):
    class mysuite(lcc.TestSuite):
        @lcc.tags("tag1")
        class subsuite1(lcc.TestSuite):
            @lcc.test("test1")
            def baz(self):
                pass
            
        @lcc.tags("tag2")
        class subsuite2(lcc.TestSuite):
            @lcc.test("test2")
            def test2(self):
                pass

    filter = Filter()
    filter.tags.append("tag2")
    
    run_testsuite(mysuite, filter=filter)
    
    assert reporting_session.test_nb == 1
    assert reporting_session.last_test == "test2"

def test_filter_tag_on_suite_negative(reporting_session):
    class mysuite(lcc.TestSuite):
        @lcc.tags("tag1")
        class subsuite1(lcc.TestSuite):
            @lcc.test("test1")
            def baz(self):
                pass
            
        @lcc.tags("tag2")
        class subsuite2(lcc.TestSuite):
            @lcc.test("test2")
            def test2(self):
                pass

    filter = Filter()
    filter.tags.append("-tag2")
    
    run_testsuite(mysuite, filter=filter)
    
    assert reporting_session.test_nb == 1
    assert reporting_session.last_test == "baz"

def test_filter_property_on_test(reporting_session):
    class mysuite(lcc.TestSuite):
        class subsuite(lcc.TestSuite):
            @lcc.test("test1")
            def baz(self):
                pass
            
            @lcc.prop("myprop", "foo")
            @lcc.test("test2")
            def test2(self):
                pass

    filter = Filter()
    filter.properties["myprop"] = "foo"
    
    run_testsuite(mysuite, filter=filter)
    
    assert reporting_session.test_nb == 1
    assert reporting_session.last_test == "test2"

def test_filter_property_on_test_negative(reporting_session):
    class mysuite(lcc.TestSuite):
        class subsuite(lcc.TestSuite):
            @lcc.prop("myprop", "bar")
            @lcc.test("test1")
            def baz(self):
                pass
            
            @lcc.prop("myprop", "foo")
            @lcc.test("test2")
            def test2(self):
                pass

    filter = Filter()
    filter.properties["myprop"] = "-foo"
    
    run_testsuite(mysuite, filter=filter)
    
    assert reporting_session.test_nb == 1
    assert reporting_session.last_test == "baz"

def test_filter_property_on_suite(reporting_session):
    class mysuite(lcc.TestSuite):
        @lcc.prop("myprop", "foo")
        class subsuite1(lcc.TestSuite):
            @lcc.test("test1")
            def baz(self):
                pass
            
        @lcc.prop("myprop", "bar")
        class subsuite2(lcc.TestSuite):
            @lcc.test("test2")
            def test2(self):
                pass

    filter = Filter()
    filter.properties["myprop"] = "bar"
    
    run_testsuite(mysuite, filter=filter)
    
    assert reporting_session.test_nb == 1
    assert reporting_session.last_test == "test2"

def test_filter_property_on_suite_negative(reporting_session):
    class mysuite(lcc.TestSuite):
        @lcc.prop("myprop", "foo")
        class subsuite1(lcc.TestSuite):
            @lcc.test("test1")
            def baz(self):
                pass
            
        @lcc.prop("myprop", "bar")
        class subsuite2(lcc.TestSuite):
            @lcc.test("test2")
            def test2(self):
                pass

    filter = Filter()
    filter.properties["myprop"] = "-bar"
    
    run_testsuite(mysuite, filter=filter)
    
    assert reporting_session.test_nb == 1
    assert reporting_session.last_test == "baz"

def test_filter_link_on_test(reporting_session):
    class mysuite(lcc.TestSuite):
        class subsuite(lcc.TestSuite):
            @lcc.test("test1")
            def baz(self):
                pass
            
            @lcc.link("http://bug.trac.ker/1234", "#1234")
            @lcc.test("test2")
            def test2(self):
                pass

    filter = Filter()
    filter.link_names.append("#1234")
    
    run_testsuite(mysuite, filter=filter)
    
    assert reporting_session.test_nb == 1
    assert reporting_session.last_test == "test2"

def test_filter_link_on_test_negative(reporting_session):
    class mysuite(lcc.TestSuite):
        class subsuite(lcc.TestSuite):
            @lcc.test("test1")
            def baz(self):
                pass
            
            @lcc.link("http://bug.trac.ker/1234", "#1234")
            @lcc.test("test2")
            def test2(self):
                pass

    filter = Filter()
    filter.link_names.append("-#1234")
    
    run_testsuite(mysuite, filter=filter)
    
    assert reporting_session.test_nb == 1
    assert reporting_session.last_test == "baz"

def test_filter_link_on_suite(reporting_session):
    class mysuite(lcc.TestSuite):
        @lcc.link("http://bug.trac.ker/1234", "#1234")
        class subsuite1(lcc.TestSuite):
            @lcc.test("test1")
            def baz(self):
                pass
            
        @lcc.link("http://bug.trac.ker/1235", "#1235")
        class subsuite2(lcc.TestSuite):
            @lcc.test("test2")
            def test2(self):
                pass

    filter = Filter()
    filter.link_names.append("#1235")
    
    run_testsuite(mysuite, filter=filter)
    
    assert reporting_session.test_nb == 1
    assert reporting_session.last_test == "test2"

def test_filter_link_on_suite_negative(reporting_session):
    class mysuite(lcc.TestSuite):
        @lcc.link("http://bug.trac.ker/1234", "#1234")
        class subsuite1(lcc.TestSuite):
            @lcc.test("test1")
            def baz(self):
                pass
            
        @lcc.link("http://bug.trac.ker/1235", "#1235")
        class subsuite2(lcc.TestSuite):
            @lcc.test("test2")
            def test2(self):
                pass

    filter = Filter()
    filter.link_names.append("-#1235")
    
    run_testsuite(mysuite, filter=filter)
    
    assert reporting_session.test_nb == 1
    assert reporting_session.last_test == "baz"

def test_filter_path_on_suite_and_tag_on_test(reporting_session):
    class mysuite(lcc.TestSuite):
        class subsuite(lcc.TestSuite):
            @lcc.test("test1")
            def baz(self):
                pass
             
            @lcc.tags("tag1")
            @lcc.test("test2")
            def test2(self):
                pass
 
    filter = Filter()
    filter.path.append("mysuite.subsuite")
    filter.tags.append("tag1")
      
    run_testsuite(mysuite, filter=filter)
      
    assert reporting_session.test_nb == 1
    assert reporting_session.last_test == "test2"

def test_filter_path_on_suite_and_negative_tag_on_test(reporting_session):
    class mysuite(lcc.TestSuite):
        class subsuite(lcc.TestSuite):
            @lcc.test("test1")
            def baz(self):
                pass
             
            @lcc.tags("tag1")
            @lcc.test("test2")
            def test2(self):
                pass
 
    filter = Filter()
    filter.path.append("mysuite.subsuite")
    filter.tags.append("-tag1")
      
    run_testsuite(mysuite, filter=filter)
      
    assert reporting_session.test_nb == 1
    assert reporting_session.last_test == "baz"

def test_filter_description_on_suite_and_link_on_test(reporting_session):
    class mysuite(lcc.TestSuite):
        class subsuite(lcc.TestSuite):
            @lcc.test("test1")
            def test1(self):
                pass
        
        class subsuite2(lcc.TestSuite):
            description = "Sub suite 2"
            
            @lcc.link("http://my.bug.trac.ker/1234", "#1234")
            @lcc.test("test2")
            def test2(self):
                pass
            
            @lcc.test("test3")
            def test3(self):
                pass
 
    filter = Filter()
    filter.description.append("Sub suite 2")
    filter.link_names.append("#1234")
      
    run_testsuite(mysuite, filter=filter)
      
    assert reporting_session.test_nb == 1
    assert reporting_session.last_test == "test2"
 
def test_filter_path_and_tag_on_suite(reporting_session):
    class mysuite(lcc.TestSuite):
        @lcc.tags("foo")
        class subsuite1(lcc.TestSuite):
            @lcc.test("test1")
            def test1(self):
                pass
        
        @lcc.tags("foo")
        class subsuite2(lcc.TestSuite):             
            @lcc.test("test2")
            def test2(self):
                pass
 
    filter = Filter()
    filter.path.append("mysuite.subsuite1")
    filter.tags.append("foo")
      
    run_testsuite(mysuite, filter=filter)
      
    assert reporting_session.test_nb == 1
    assert reporting_session.last_test == "test1"

def test_filter_path_and_tag_on_test(reporting_session):
    class mysuite(lcc.TestSuite):
        class subsuite1(lcc.TestSuite):
            @lcc.tags("foo")
            @lcc.test("test1")
            def test1(self):
                pass
        
        class subsuite2(lcc.TestSuite):             
            @lcc.tags("foo")
            @lcc.test("test2")
            def test2(self):
                pass
            
            @lcc.test("test3")
            def test3(self):
                pass
 
    filter = Filter()
    filter.path.append("mysuite.subsuite2.*")
    filter.tags.append("foo")
      
    run_testsuite(mysuite, filter=filter)
      
    assert reporting_session.test_nb == 1
    assert reporting_session.last_test == "test2"

def test_filter_path_and_negative_tag_on_test(reporting_session):
    class mysuite(lcc.TestSuite):
        class subsuite1(lcc.TestSuite):
            @lcc.tags("foo")
            @lcc.test("test1")
            def test1(self):
                pass
        
        class subsuite2(lcc.TestSuite):             
            @lcc.tags("foo")
            @lcc.test("test2")
            def test2(self):
                pass
            
            @lcc.test("test3")
            def test3(self):
                pass
 
    filter = Filter()
    filter.path.append("mysuite.subsuite2.*")
    filter.tags.append("-foo")
      
    run_testsuite(mysuite, filter=filter)
      
    assert reporting_session.test_nb == 1
    assert reporting_session.last_test == "test3"

def test_is_empty_true():
    filt = Filter()
    assert filt.is_empty() == True
 
def test_is_empty_false():
    def do_test(attr, val):
        filt = Filter()
        assert hasattr(filt, attr)
        setattr(filt, attr, val)
        assert filt.is_empty() == False
     
    do_test("path", "foo")
    do_test("description", "foo")
    do_test("tags", "foo")
    do_test("properties", "foo")
    do_test("link_names", "foo")
